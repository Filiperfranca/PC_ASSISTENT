import json
from pathlib import Path

import cv2
import numpy as np


FACES_DIR = Path("app") / "data" / "faces"
MODELS_DIR = Path("app") / "data" / "models"

MODEL_PATH = MODELS_DIR / "lbph_model.yml"
LABELS_PATH = MODELS_DIR / "labels.json"


def load_training_data():
    faces = []
    labels = []
    label_map = {}

    if not FACES_DIR.exists():
        raise RuntimeError(f"Pasta de faces não encontrada: {FACES_DIR}")

    user_dirs = sorted([path for path in FACES_DIR.iterdir() if path.is_dir()])

    if not user_dirs:
        raise RuntimeError(f"Nenhum usuário cadastrado em: {FACES_DIR}")

    for label_id, user_dir in enumerate(user_dirs):
        user_name = user_dir.name
        label_map[label_id] = user_name

        image_paths = sorted(
            list(user_dir.glob("*.jpg"))
            + list(user_dir.glob("*.jpeg"))
            + list(user_dir.glob("*.png"))
        )

        if not image_paths:
            print(f"Aviso: usuário sem imagens: {user_name}")
            continue

        for image_path in image_paths:
            image = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)

            if image is None:
                print(f"Aviso: não foi possível ler imagem: {image_path}")
                continue

            image = cv2.resize(image, (200, 200))

            faces.append(image)
            labels.append(label_id)

    if not faces:
        raise RuntimeError("Nenhuma imagem válida encontrada para treinamento.")

    return faces, np.array(labels, dtype=np.int32), label_map


def train_model(faces, labels):
    recognizer = cv2.face.LBPHFaceRecognizer_create(
        radius=1,
        neighbors=8,
        grid_x=8,
        grid_y=8,
    )

    recognizer.train(faces, labels)

    return recognizer


def save_model(recognizer, label_map):
    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    recognizer.write(str(MODEL_PATH))

    labels_as_json = {
        str(label_id): user_name
        for label_id, user_name in label_map.items()
    }

    with open(LABELS_PATH, "w", encoding="utf-8") as file:
        json.dump(labels_as_json, file, indent=4, ensure_ascii=False)


def main():
    print("=" * 60)
    print("TREINAMENTO DO RECONHECEDOR FACIAL")
    print("=" * 60)

    faces, labels, label_map = load_training_data()

    print(f"Usuários encontrados: {len(label_map)}")
    print(f"Total de imagens: {len(faces)}")
    print(f"Labels: {label_map}")

    recognizer = train_model(faces, labels)

    save_model(recognizer, label_map)

    print()
    print("Treinamento concluído com sucesso.")
    print(f"Modelo salvo em: {MODEL_PATH}")
    print(f"Labels salvos em: {LABELS_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()