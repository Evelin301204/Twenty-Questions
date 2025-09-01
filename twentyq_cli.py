
import os, glob, pandas as pd, numpy as np, textwrap
import warnings
warnings.simplefilter(action="ignore", category=FutureWarning)
BOOL_TRUE = {"true","1","sí","si","yes","y","t","verdadero"}
def norm_path(p):
    return os.path.abspath(p)

def list_csvs(path):
    files = glob.glob(os.path.join(path, "*.csv"))
    return sorted(files)

def normalize_booleans(df, skip_cols={"nombre","subcategoria","grupo"}):
    bool_cols = [c for c in df.columns if c not in skip_cols]
    for c in bool_cols:
        if df[c].dtype != bool:
            s = df[c].astype(str).str.strip().str.lower()
            df[c] = s.isin(BOOL_TRUE)
    return bool_cols

def normalize_nombre(df):
    df["nombre"] = (
        df["nombre"]
        .astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"\s+","", regex=True)
    )
    return df

def load_datasets_from_folder(folder_path: str):
    folder_path = norm_path(folder_path)
    packs = {}
    files = list_csvs(folder_path)
    for file in files:
        try:
            df = pd.read_csv(file)
        except Exception as e:
            print(f"[WARN] No pude leer {file}: {e}")
            continue
        if df.empty or "nombre" not in df.columns:
            print(f"[WARN] Omito {os.path.basename(file)} (vacío o sin 'nombre')")
            continue
        key = os.path.splitext(os.path.basename(file))[0]
        if "subcategoria" not in df.columns:
            df["subcategoria"] = key
        normalize_nombre(df)
        bool_cols = normalize_booleans(df)
        df["grupo"] = key
        packs[key] = {"df": df, "bool_cols": bool_cols}
        print(f"[OK] {folder_path}/{key}: {df.shape[0]} filas, {len(bool_cols)} flags")
    if not packs:
        print(f"[INFO] Sin CSV en {folder_path}")
    return packs

def build_pool(packs):
    frames = [p["df"] for p in packs.values() if not p["df"].empty]
    if not frames:
        return pd.DataFrame()
    pool = pd.concat(frames, ignore_index=True, sort=False)
    for c in pool.columns:
        if c not in {"nombre","subcategoria","grupo"}:
            pool[c] = pool[c].fillna(False).astype(bool)
    return pool

def yn_parse(ans: str):
    a = ans.strip().lower()
    if a in {"sí","si","s","y","yes"}: return True
    if a in {"no","n"}: return False
    if a in {"no se","nose","idk","?"}: return None
    return None

def ask_yn(q):
    ans = input(q + " (sí/no/no sé) > ").strip().lower()
    return yn_parse(ans)

def pick_next_flag_entropy(df, available_flags):
    if len(df) <= 1: 
        return None
    import numpy as np
    best, best_score, best_coverage = None, -1.0, -1
    n = len(df)
    for col in available_flags:
        if col not in df.columns: 
            continue
        t = int(df[col].sum())
        if t == 0 or t == n:
            continue
        p = t / n
        score = -(p*np.log2(p) + (1-p)*np.log2(1-p))
        coverage = min(t, n - t)
        if (score > best_score) or (np.isclose(score, best_score) and coverage > best_coverage):
            best, best_score, best_coverage = col, score, coverage
    return best

def sub_flow(target_group: str, POOL: pd.DataFrame, DATASETS: dict, max_questions=8):
    if target_group not in DATASETS:
        print(f"[WARN] No encuentro subcategoría '{target_group}'. Muestro candidatos del pool completo.")
        df = POOL.copy()
        flags = [c for c in df.columns if c not in {"nombre","subcategoria","grupo"} and df[c].dtype==bool]
    else:
        df = POOL[POOL["grupo"] == target_group].copy()
        flags = [c for c in DATASETS[target_group]["bool_cols"] if c in df.columns]

    used, no_se = [], 0
    print(f"\n— Preguntas dentro de {target_group} — (sí/no/no sé, 'salir' para terminar)\n")
    while len(df) > 3 and len(used) < max_questions:
        col = pick_next_flag_entropy(df, [c for c in flags if c not in used])
        if not col:
            break
        ans = input(f"[{len(df)} {target_group}] {col.replace('_',' ').capitalize()}? > ").strip().lower()
        if ans == "salir":
            break
        yn = yn_parse(ans)
        if yn is None:
            used.append(col); no_se += 1
            print(f"→ No sé; seguimos. (no_sé={no_se})")
            continue
        before = len(df)
        df = df[df[col] == yn]
        used.append(col); no_se = 0
        print(f"→ Filtro {col}={yn} | {before}→{len(df)}")

    print("\n— Resultado —")
    cols_show = ["nombre","grupo","subcategoria"] + [c for c in used if c in df.columns][:6]
    if df.empty:
        print("(Sin candidatos tras filtros)")
    else:
        print(df[cols_show].head(12).to_string(index=False))
    return df

def generic_router(pool: pd.DataFrame, pares):
    print()
    title = pares.get("_title", "— Router —")
    print(title, "\n")
    existentes = set(pool["grupo"].unique())
    for key, question in pares["orden"]:
        if key in existentes:
            r = ask_yn(question)
            if r is True:
                return key
    return pool["grupo"].value_counts().idxmax()

def router_personas(pool):
    pares = {
        "_title": "— Router de subcategorías (Personas) —",
        "orden": [
            ("Personajes", "¿Es un personaje específico (real o de ficción)?"),
            ("Profesiones","¿Se refiere a una profesión u oficio?"),
            ("Culturales", "¿Es una identidad cultural/étnica (maya, vikingo…)?"),
            ("Roles",      "¿Es un rol social (alumno, jefe, voluntario…)?"),
            ("Colectivos", "¿Es un colectivo humano (familia, tribu, nación…)?"),
        ]
    }
    return generic_router(pool, pares)

def router_conceptos(pool):
    pares = {
        "_title": "— Router de subcategorías (Conceptos) —",
        "orden": [
            ("Emociones",   "¿Es un sentimiento o emoción (amor, miedo, tristeza…)?"),
            ("Valores",     "¿Es un valor o principio (justicia, libertad…)?"),
            ("Cualidades",  "¿Es una cualidad o atributo (belleza, inteligencia…)?"),
            ("Fenomenos",   "¿Es un fenómeno universal (tiempo, espacio…)?"),
            ("Ideas",       "¿Es una idea o constructo social (democracia, religión…)?"),
            ("Eventos",     "¿Es un evento o hecho abstracto (guerra, cambio…)?"),
        ]
    }
    return generic_router(pool, pares)

def router_adjetivos(pool):
    pares = {
        "_title": "— Router de subcategorías (Adjetivos) —",
        "orden": [
            ("Colores",       "¿Es un color?"),
            ("Cualitativos",  "¿Es una cualidad (grande, fuerte, claro…)?"),
            ("Cuantitativos", "¿Indica cantidad (muchos, pocos, doble…)?"),
            ("Relacionales",  "¿Indica pertenencia/ámbito (mexicano, digital, escolar…)?"),
            ("Posesivos",     "¿Es un posesivo (mi, tu, su, nuestro…)?"),
        ]
    }
    return generic_router(pool, pares)

def router_animales(pool):
    pares = {
        "_title": "— Router de subcategorías (Animales) —",
        "orden": [
            ("Moluscos", "¿Es un molusco (caracol, almeja, pulpo…)?"),
        ]
    }
    return generic_router(pool, pares)

def router_objetos(pool):
    pares = {
        "_title": "— Router de subcategorías (Objetos) —",
        "orden": [
            ("Tecnologia", "¿Es tecnología/electrónico?"),
            ("Muebles",    "¿Se usa en casa (mueble/enser)?"),
            ("Herramientas","¿Es una herramienta o utensilio?"),
            ("Vehiculos",  "¿Es un vehículo?"),
            ("Ropa",       "¿Es ropa o accesorio?"),
        ]
    }
    return generic_router(pool, pares)

def router_lugares(pool):
    pares = {
        "_title": "— Router de subcategorías (Lugares) —",
        "orden": [
            ("Naturales", "¿Es un lugar natural (río, bosque, montaña…)?"),
            ("Artificiales","¿Es un lugar hecho por humanos (ciudad, país, edificio…)?"),
        ]
    }
    return generic_router(pool, pares)

def router_cuerpo(pool):
    pares = {
        "_title": "— Router de subcategorías (Cuerpo) —",
        "orden": [
            ("Parte", "¿Es una parte del cuerpo?"),
        ]
    }
    return generic_router(pool, pares)

def router_verbos(pool):
    pares = {
        "_title": "— Router de subcategorías (Verbos) —",
        "orden": [
            ("Verbo", "¿Es un verbo en infinitivo?"),
        ]
    }
    return generic_router(pool, pares)

class Node:
    def __init__(self, text=None, yes=None, no=None, leaf=None):
        self.text = text
        self.yes = yes
        self.no = no
        self.leaf = leaf
    def is_leaf(self):
        return self.leaf is not None

def build_root():
    return Node(
        text="¿Es un ser vivo?",
        yes=Node(
            text="¿Es humano?",
            yes=Node(leaf="PERSONAS_FLOW"),
            no=Node(
                text="¿Es un animal?",
                yes=Node(leaf="ANIMALES_FLOW"),
                no=Node(
                    text="¿Es una planta?",
                    yes=Node(leaf="PLANTAS_FLOW"),
                    no=Node(
                        text="¿Es un hongo/microbio?",
                        yes=Node(leaf="HONGOS_FLOW"),
                        no=Node(leaf="DESCARTADO_VIVOS")
                    )
                )
            )
        ),
        no=Node(
            text="¿Es un objeto?",
            yes=Node(leaf="OBJETOS_FLOW"),
            no=Node(
                text="¿Es un lugar?",
                yes=Node(leaf="LUGARES_FLOW"),
                no=Node(
                    text="¿Es un concepto abstracto?",
                    yes=Node(leaf="CONCEPTOS_FLOW"),
                    no=Node(
                        text="¿Es un verbo / acción?",
                        yes=Node(leaf="VERBOS_FLOW"),
                        no=Node(
                            text="¿Es un adjetivo / cualidad?",
                            yes=Node(leaf="ADJETIVOS_FLOW"),
                            no=Node(leaf="NO_CLASIFICADO")
                        )
                    )
                )
            )
        )
    )

POOLS = {}
DATASETS = {}

def ensure_category_loaded(category_name: str, folder_candidates):
    if category_name in POOLS and not POOLS[category_name].empty:
        return
    for p in folder_candidates:
        if os.path.isdir(p):
            packs = load_datasets_from_folder(p)
            POOLS[category_name] = build_pool(packs)
            DATASETS[category_name] = packs
            if not POOLS[category_name].empty:
                print(f"[OK] {category_name}: {POOLS[category_name].shape}")
                return
    POOLS[category_name] = pd.DataFrame()
    DATASETS[category_name] = {}

def traverse(node: Node):
    if node.is_leaf():
        leaf = node.leaf

        if leaf == "PERSONAS_FLOW":
            ensure_category_loaded("Personas", ["./Personas"])
            target = router_personas(POOLS["Personas"])
            sub_flow(target, POOLS["Personas"], DATASETS["Personas"])
            return "Personas"

        if leaf == "CONCEPTOS_FLOW":
            ensure_category_loaded("Conceptos", ["./Conceptos"])
            target = router_conceptos(POOLS["Conceptos"])
            sub_flow(target, POOLS["Conceptos"], DATASETS["Conceptos"])
            return "Conceptos"

        if leaf == "ADJETIVOS_FLOW":
            ensure_category_loaded("Adjetivos", ["./Adjetivos"])
            target = router_adjetivos(POOLS["Adjetivos"])
            sub_flow(target, POOLS["Adjetivos"], DATASETS["Adjetivos"])
            return "Adjetivos"

        if leaf == "ANIMALES_FLOW":
            ensure_category_loaded("Animales", ["./Animales"])
            target = router_animales(POOLS["Animales"])
            sub_flow(target, POOLS["Animales"], DATASETS["Animales"])
            return "Animales"

        if leaf == "OBJETOS_FLOW":
            ensure_category_loaded("Objetos", ["./Objetos"])
            target = router_objetos(POOLS["Objetos"])
            sub_flow(target, POOLS["Objetos"], DATASETS["Objetos"])
            return "Objetos"

        if leaf == "LUGARES_FLOW":
            ensure_category_loaded("Lugares", ["./Lugares"])
            target = router_lugares(POOLS["Lugares"])
            sub_flow(target, POOLS["Lugares"], DATASETS["Lugares"])
            return "Lugares"

        if leaf == "VERBOS_FLOW":
            ensure_category_loaded("Verbos", ["./Verbos"])
            target = router_verbos(POOLS["Verbos"])
            sub_flow(target, POOLS["Verbos"], DATASETS["Verbos"])
            return "Verbos"

        if leaf == "PLANTAS_FLOW":
            print("Aún no hay datasets de Plantas. (pendiente)")
            return "Plantas (pendiente)"

        if leaf == "HONGOS_FLOW":
            ensure_category_loaded("Hongos_Microbios", ["./Hongos_Microbios"])
            if POOLS["Hongos_Microbios"].empty:
                print("Aún no hay datasets de Hongos/Microbios.")
                return "Hongos/Microbios (pendiente)"
            target = POOLS["Hongos_Microbios"]["grupo"].value_counts().idxmax()
            sub_flow(target, POOLS["Hongos_Microbios"], DATASETS["Hongos_Microbios"])
            return "Hongos/Microbios"

        if leaf == "DESCARTADO_VIVOS":
            print("No es animal, planta ni hongo/microbio. (fin)")
            return "Descartado"

        if leaf == "NO_CLASIFICADO":
            print("No encaja en ninguna categoría conocida. (fin)")
            return "No clasificado"

        print(f"Categoría final: {leaf}")
        return leaf

    # pregunta binaria
    while True:
        ans = input(f"{node.text} (sí/no) > ").strip().lower()
        yn = yn_parse(ans)
        if yn is None:
            print("Responde 'sí' o 'no'.")
            continue
        return traverse(node.yes if yn else node.no)

def print_rules():
    txt = """
    ===================================
       Bienvenido a TwentyQ (CLI)
    ===================================
    REGLAS DEL JUEGO:
    1. Ingresa una sola palabra; no se aceptan compuestas.
    2. Los verbos deben ir en infinitivo (correr, saltar).
    3. Responde con 'sí', 'no' o 'no sé' a las preguntas.
    4. Escribe 'salir' cuando estés dentro de un flujo para terminar.
    ===================================
    """
    print(textwrap.dedent(txt))

def main():
    print_rules()
    root = build_root()
    traverse(root)

if __name__ == '__main__':
    main()
