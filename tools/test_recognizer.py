import json
from pathlib import Path

import cv2


MODEL_PATH = Path("app") / "data" / "models" / "lbph_model.yml"
LABELS_PATH = Path("app") / "data" / "models" / "labels.json"


def load_face_detector():
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

    detector = cv2.CascadeClassifier(cascade_path)

    if detector.empty():
        raise RuntimeError(f"Não foi possível carregar detector facial: {cascade_path}")

    return detector


def load_recognizer():
    if not MODEL_PATH.exists():
        raise RuntimeError(f"Modelo não encontrado: {MODEL_PATH}")

    if not LABELS_PATH.exists():
        raise RuntimeError(f"Labels não encontrados: {LABELS_PATH}")

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(str(MODEL_PATH))

    with open(LABELS_PATH, "r", encoding="utf-8") as file:
        labels = json.load(file)

    return recognizer, labels


def normalize_face(gray_frame, face_box):
    x, y, width, height = face_box

    face = gray_frame[y:y + height, x:x + width]
    face = cv2.resize(face, (200, 200))
    face = cv2.equalizeHist(face)

    return face


def detect_main_face(detector, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.08,
        minNeighbors=6,
        minSize=(90, 90),
    )

    faces = [face for face in faces if face[2] * face[3] >= 120 * 120]

    if len(faces) == 0:
        return None, gray

    main_face = max(faces, key=lambda face: face[2] * face[3])

    return main_face, gray


def main():
    detector = load_face_detector()
    recognizer, labels = load_recognizer()

    capture = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not capture.isOpened():
        raise RuntimeError("Não foi possível abrir a câmera.")

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    capture.set(cv2.CAP_PROP_FPS, 10)

    print("=" * 60)
    print("TESTE DO RECONHECEDOR")
    print("=" * 60)
    print("Pressione Q para sair.")
    print()
    print("Observação:")
    print("No LBPH, confidence menor geralmente significa melhor match.")
    print("=" * 60)

    try:
        while True:
            success, frame = capture.read()

            if not success or frame is None:
                continue

            face_box, gray = detect_main_face(detector, frame)

            if face_box is not None:
                x, y, width, height = face_box

                face = normalize_face(gray, face_box)

                label_id, confidence = recognizer.predict(face)
                user_name = labels.get(str(label_id), "unknown")

                text = f"{user_name} | conf={confidence:.2f}"

                cv2.rectangle(
                    frame,
                    (x, y),
                    (x + width, y + height),
                    (0, 255, 0),
                    2,
                )

                cv2.putText(
                    frame,
                    text,
                    (x, max(y - 10, 25)),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.7,
                    (0, 255, 0),
                    2,
                )

                print(f"Reconhecido: {user_name} | confidence={confidence:.2f}")

            cv2.imshow("Teste Reconhecimento Facial", frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                break

    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()