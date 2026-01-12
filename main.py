"""
TrackingMaster v0.1 - Foundation
Point d'entrée principal de l'application.

Contrôles:
    Q / ESC  : Quitter
    SPACE    : Pause / Reprendre
    S        : Screenshot
    I        : Afficher/Masquer les infos
"""

import cv2
import sys
import time
from src.camera import Camera, list_available_cameras


# Configuration
WINDOW_NAME = "TrackingMaster v0.1"
DEFAULT_CAMERA = 0


def draw_info_overlay(frame, fps: float, is_paused: bool, show_info: bool):
    """Dessine les informations sur la frame."""
    if not show_info:
        return frame

    height, width = frame.shape[:2]

    # Informations à afficher
    info_lines = [
        f"FPS: {fps:.1f}",
        f"Resolution: {width}x{height}",
        f"Status: {'PAUSED' if is_paused else 'RUNNING'}",
        "[Q] Quit [SPACE] Pause [S] Shot [I] Info"
    ]

    # Calculer la taille du fond
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 1
    padding = 15
    line_height = 22

    # Trouver la largeur max du texte
    max_width = 0
    for line in info_lines:
        (text_width, _), _ = cv2.getTextSize(line, font, font_scale, thickness)
        max_width = max(max_width, text_width)

    # Dimensions du rectangle
    rect_width = max_width + padding * 2
    rect_height = len(info_lines) * line_height + padding * 2 - 5

    # Fond semi-transparent
    overlay = frame.copy()
    cv2.rectangle(overlay, (10, 10), (10 + rect_width, 10 + rect_height), (0, 0, 0), -1)
    frame = cv2.addWeighted(overlay, 0.6, frame, 0.4, 0)

    # Dessiner le texte
    y_offset = 10 + padding + 12
    for line in info_lines:
        if "PAUSED" in line:
            color = (0, 255, 255)  # Jaune
        elif "RUNNING" in line:
            color = (0, 255, 0)  # Vert
        else:
            color = (255, 255, 255)  # Blanc

        cv2.putText(
            frame, line,
            (10 + padding, y_offset),
            font, font_scale, color, thickness, cv2.LINE_AA
        )
        y_offset += line_height

    return frame


def draw_pause_indicator(frame):
    """Affiche un indicateur de pause au centre."""
    height, width = frame.shape[:2]
    center_x, center_y = width // 2, height // 2

    # Icône pause (deux barres)
    bar_width = 20
    bar_height = 60
    gap = 20

    cv2.rectangle(
        frame,
        (center_x - gap - bar_width, center_y - bar_height // 2),
        (center_x - gap, center_y + bar_height // 2),
        (255, 255, 255), -1
    )
    cv2.rectangle(
        frame,
        (center_x + gap, center_y - bar_height // 2),
        (center_x + gap + bar_width, center_y + bar_height // 2),
        (255, 255, 255), -1
    )

    return frame


def select_camera(cameras: list) -> int:
    """
    Permet à l'utilisateur de sélectionner une caméra.

    Args:
        cameras: Liste des caméras disponibles

    Returns:
        ID de la caméra sélectionnée, ou -1 si annulé
    """
    valid_ids = [cam["id"] for cam in cameras]

    while True:
        try:
            if len(cameras) == 1:
                cam = cameras[0]
                choice = input(f"\nInitialiser la camera {cam['id']}? (O/n): ").strip().lower()
                if choice in ("", "o", "oui", "y", "yes"):
                    return cam["id"]
                elif choice in ("n", "non", "no"):
                    print("Annulation.")
                    sys.exit(0)
                else:
                    print("Repondez par O (oui) ou N (non)")
            else:
                choice = input(f"\nQuelle camera initialiser? {valid_ids}: ").strip()
                selected_id = int(choice)

                if selected_id in valid_ids:
                    return selected_id
                else:
                    print(f"Choix invalide. Options: {valid_ids}")
        except ValueError:
            print(f"Entrez un nombre parmi {valid_ids}")
        except KeyboardInterrupt:
            print("\nAnnulation.")
            sys.exit(0)


def main():
    """Fonction principale."""
    print("=" * 50)
    print("  TrackingMaster v0.1 - Foundation")
    print("=" * 50)

    # Scanner les caméras disponibles
    print("\n[1/3] Recherche des cameras...")
    cameras = list_available_cameras()

    if not cameras:
        print("  ERREUR: Aucune camera detectee!")
        print("  Verifiez que votre webcam est connectee et non utilisee par une autre application.")
        sys.exit(1)

    print(f"\n  {len(cameras)} camera(s) disponible(s):")
    for cam in cameras:
        print(f"    [{cam['id']}] {cam['name']}")
        print(f"        Resolution: {cam['resolution']} | FPS: {cam['fps']:.0f} | Backend: {cam['backend']}")

    # Sélection de la caméra
    selected_id = select_camera(cameras)

    # Initialiser la caméra sélectionnée
    print(f"\n[2/3] Initialisation de la camera {selected_id}...")
    camera = Camera(camera_id=selected_id)

    if not camera.start():
        print(f"  ERREUR: Impossible d'ouvrir la camera {selected_id}!")
        sys.exit(1)

    resolution = camera.get_resolution()

    print(f"\n[3/3] Demarrage...")
    print(f"  Camera prete: {resolution[0]}x{resolution[1]}")
    print("\nContrôles:")
    print("  Q / ESC  : Quitter")
    print("  SPACE    : Pause / Reprendre")
    print("  S        : Screenshot")
    print("  I        : Afficher/Masquer infos")
    print("-" * 50)

    # Variables pour le calcul du FPS
    prev_time = time.time()
    fps = 0.0
    show_info = True

    try:
        while True:
            # Lire une frame
            success, frame = camera.read_frame()

            if not success:
                print("ERREUR: Impossible de lire la frame")
                break

            # Calculer le FPS
            current_time = time.time()
            fps = 1.0 / (current_time - prev_time) if (current_time - prev_time) > 0 else 0
            prev_time = current_time

            # Dessiner les overlays
            frame = draw_info_overlay(frame, fps, camera.is_paused, show_info)

            if camera.is_paused:
                frame = draw_pause_indicator(frame)

            # Afficher la frame
            cv2.imshow(WINDOW_NAME, frame)

            # Gérer les entrées clavier
            key = cv2.waitKey(1) & 0xFF

            if key == ord('q') or key == 27:  # Q ou ESC
                print("\nFermeture...")
                break

            elif key == ord(' '):  # SPACE
                paused = camera.toggle_pause()
                print(f"{'Pause' if paused else 'Reprise'}")

            elif key == ord('s'):  # S
                filepath = camera.take_screenshot(camera.last_frame)
                if filepath:
                    print(f"Screenshot sauvegardé: {filepath}")

            elif key == ord('i'):  # I
                show_info = not show_info

    except KeyboardInterrupt:
        print("\nInterruption par l'utilisateur")

    finally:
        # Nettoyage
        camera.release()
        cv2.destroyAllWindows()
        print("TrackingMaster fermé.")


if __name__ == "__main__":
    main()
