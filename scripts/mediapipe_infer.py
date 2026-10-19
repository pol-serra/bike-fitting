"""Ejecuta MediaPipe Pose (Tasks API) fuera del kernel de Jupyter.

Se invoca como subproceso para que un posible `abort()` nativo de MediaPipe
(p. ej. el fallo de Metal en algunos builds de macOS) no tumbe el kernel.

Uso:
    python mediapipe_infer.py <modelo.task> <imagen> [min_pose_detection_confidence]

Salida (stdout): un JSON con `{"width", "height", "landmarks": [{"x","y","visibility"}, ...]}`.
En caso de no detectar pose devuelve `landmarks: []`. Los errores van a stderr con
código de salida != 0.
"""

from __future__ import annotations

import json
import sys

import mediapipe as mp
from mediapipe.tasks import python as mp_python
from mediapipe.tasks.python import vision as mp_vision


def main() -> int:
    if len(sys.argv) < 3:
        print("uso: mediapipe_infer.py <modelo.task> <imagen> [conf]", file=sys.stderr)
        return 2

    model_path, image_path = sys.argv[1], sys.argv[2]
    confidence = float(sys.argv[3]) if len(sys.argv) > 3 else 0.5

    options = mp_vision.PoseLandmarkerOptions(
        base_options=mp_python.BaseOptions(model_asset_path=model_path),
        running_mode=mp_vision.RunningMode.IMAGE,
        num_poses=1,
        min_pose_detection_confidence=confidence,
    )
    landmarker = mp_vision.PoseLandmarker.create_from_options(options)

    image = mp.Image.create_from_file(image_path)
    result = landmarker.detect(image)

    landmarks = []
    if result.pose_landmarks:
        for point in result.pose_landmarks[0]:
            landmarks.append({
                "x": float(point.x),
                "y": float(point.y),
                "visibility": float(point.visibility),
            })

    json.dump({"width": image.width, "height": image.height, "landmarks": landmarks}, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
