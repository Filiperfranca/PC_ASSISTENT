import argparse
import time
from pathlib import Path

import cv2


def parse_args():
    parser = argparse.ArgumentParser(description="Cadastrar amostras faciais de um usuário.")

    parser.add_argument(
        "--user",
        required=True,
        help="Identificador do usuário a ser cadastrado. Exemplo: login.institucional",
    )

    parser.add_argument(
        "--samples",
        type=int,
        default=40,
        help="Quantidade de amostras faciais para capturar.",
    )

    parser.add_argument(
        "--camera",
        type=int,
        default=0,
        help="Índice da câmera.",
    )

    parser.add_argument(
        "--interval",
        type=float,
        default=0.25,
        help="Intervalo mínimo entre capturas em segundos.",
    )

    return parser.parse_args()


def load_face_detector():
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"

    detector = cv2.CascadeClassifier(cascade_path)

    if detector.empty():
        raise RuntimeError(f"Não foi possível carregar detector facial: {cascade_path}")

    return detector


def detect_main_face(detector, frame):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = detector.detectMultiScale(
        gray,
        scaleFactor=1.08,
        minNeighbors=6,
        minSize=(90, 90),
    )

    if len(faces) == 0:
        return None, gray

    faces = [face for face in faces if face[2] * face[3] >= 120 * 120]

    if len(faces) == 0:
        return None, gray

    main_face = max(faces, key=lambda face: face[2] * face[3])

    return main_face, gray


def normalize_face(gray_frame, face_box):
    x, y, width, height = face_box

    face = gray_frame[y:y + height, x:x + width]

    face = cv2.resize(face, (200, 200))
    face = cv2.equalizeHist(face)

    return face


def main():
    args = parse_args()

    user_name = args.user.strip().lower()

    output_dir = Path("app") / "data" / "faces" / user_name
    output_dir.mkdir(parents=True, exist_ok=True)

    detector = load_face_detector()

    print("=" * 60)
    print("CADASTRO FACIAL")
    print("=" * 60)
    print(f"Usuário: {user_name}")
    print(f"Amostras desejadas: {args.samples}")
    print(f"Pasta de saída: {output_dir}")
    print()
    print("Instruções:")
    print("- Fique em frente à câmera.")
    print("- Mude levemente o ângulo do rosto.")
    print("- Olhe um pouco para esquerda/direita.")
    print("- Varie expressão e distância.")
    print("- Pressione Q para cancelar.")
    print("=" * 60)

    capture = cv2.VideoCapture(args.camera, cv2.CAP_DSHOW)

    if not capture.isOpened():
        raise RuntimeError(f"Não foi possível abrir câmera no índice {args.camera}")

    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    capture.set(cv2.CAP_PROP_FPS, 10)

    sample_count = 0
    last_capture_at = 0.0

    try:
        while sample_count < args.samples:
            success, frame = capture.read()

            if not success or frame is None:
                print("Falha ao capturar frame.")
                time.sleep(0.5)
                continue

            face_box, gray = detect_main_face(detector, frame)

            display_frame = frame.copy()

            if face_box is not None:
                x, y, width, height = face_box

                cv2.rectangle(
                    display_frame,
                    (x, y),
                    (x + width, y + height),
                    (0, 255, 0),
                    2,
                )

                now = time.time()

                if now - last_capture_at >= args.interval:
                    face = normalize_face(gray, face_box)

                    sample_count += 1
                    file_name = output_dir / f"{sample_count:03d}.jpg"

                    cv2.imwrite(str(file_name), face)

                    last_capture_at = now

                    print(f"Amostra salva: {file_name}")

            progress_text = f"Amostras: {sample_count}/{args.samples}"

            cv2.putText(
                display_frame,
                progress_text,
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2,
            )

            cv2.putText(
                display_frame,
                "Pressione Q para cancelar",
                (10, display_frame.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                2,
            )

            cv2.imshow("Cadastro Facial", display_frame)

            key = cv2.waitKey(1) & 0xFF

            if key == ord("q"):
                print("Cadastro cancelado pelo usuário.")
                break

        print()
        print("=" * 60)
        print(f"Cadastro finalizado. Amostras capturadas: {sample_count}")
        print("=" * 60)

    finally:
        capture.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()