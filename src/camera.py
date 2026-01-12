"""
TrackingMaster v0.1 - Camera Module
Gestion de l'accès à la webcam et des contrôles de base.
"""

import cv2
import sys
from datetime import datetime
from pathlib import Path


class Camera:
    """Classe pour gérer l'accès à la webcam et les contrôles."""

    def __init__(self, camera_id: int = 0, width: int = 1280, height: int = 720):
        """
        Initialise la caméra.

        Args:
            camera_id: ID de la caméra (0 = caméra par défaut)
            width: Largeur de la capture
            height: Hauteur de la capture
        """
        self.camera_id = camera_id
        self.width = width
        self.height = height
        self.cap = None
        self.is_paused = False
        self.last_frame = None
        self.screenshot_dir = Path("screenshots")

    def start(self, verbose: bool = True) -> bool:
        """
        Démarre la capture vidéo.

        Args:
            verbose: Afficher les messages de progression

        Returns:
            True si la caméra est ouverte avec succès, False sinon.
        """
        # Utiliser DirectShow sur Windows pour une initialisation plus rapide
        if sys.platform == "win32":
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
        else:
            self.cap = cv2.VideoCapture(self.camera_id)

        if not self.cap.isOpened():
            return False

        if verbose:
            print(f"  > Connexion a la camera {self.camera_id}... OK")

        # Réduire le buffer pour moins de latence
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        # Configuration de la résolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        # Définir le FPS cible
        self.cap.set(cv2.CAP_PROP_FPS, 30)

        if verbose:
            actual_w = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            actual_h = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"  > Configuration resolution {actual_w}x{actual_h}... OK")

        # Vérifier et créer le dossier screenshots si nécessaire
        if verbose:
            print(f"  > Verification du dossier '{self.screenshot_dir}'...", end=" ")

        if self.screenshot_dir.exists():
            if verbose:
                print("existe deja")
        else:
            self.screenshot_dir.mkdir(exist_ok=True)
            if verbose:
                print("cree")

        # Lire une première frame pour "chauffer" la caméra
        if verbose:
            print(f"  > Warmup camera...", end=" ")
        self.cap.read()
        if verbose:
            print("OK")

        return True

    def read_frame(self):
        """
        Lit une frame de la caméra.

        Returns:
            tuple: (success, frame) - success est un booléen, frame est l'image
        """
        if self.cap is None:
            return False, None

        if self.is_paused and self.last_frame is not None:
            return True, self.last_frame

        success, frame = self.cap.read()

        if success:
            # Miroir horizontal pour un affichage naturel
            frame = cv2.flip(frame, 1)
            self.last_frame = frame

        return success, frame

    def toggle_pause(self):
        """Bascule entre pause et lecture."""
        self.is_paused = not self.is_paused
        return self.is_paused

    def take_screenshot(self, frame) -> str:
        """
        Prend une capture d'écran.

        Args:
            frame: L'image à sauvegarder

        Returns:
            Le chemin du fichier sauvegardé
        """
        if frame is None:
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.screenshot_dir / f"screenshot_{timestamp}.png"
        cv2.imwrite(str(filename), frame)
        return str(filename)

    def get_fps(self) -> float:
        """Retourne le FPS de la caméra."""
        if self.cap is None:
            return 0.0
        return self.cap.get(cv2.CAP_PROP_FPS)

    def get_resolution(self) -> tuple:
        """Retourne la résolution actuelle (width, height)."""
        if self.cap is None:
            return (0, 0)
        return (
            int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        )

    def release(self):
        """Libère les ressources de la caméra."""
        if self.cap is not None:
            self.cap.release()
            self.cap = None


class CameraError(Exception):
    """Exception personnalisée pour les erreurs de caméra."""
    pass


def get_camera_names_windows() -> list:
    """
    Récupère les noms des caméras sur Windows via pygrabber (DirectShow).

    Returns:
        Liste des noms de caméras dans l'ordre
    """
    names = []

    # Utiliser pygrabber pour récupérer les noms DirectShow
    try:
        from pygrabber.dshow_graph import FilterGraph

        graph = FilterGraph()
        devices = graph.get_input_devices()
        names = list(devices.values())

        if names:
            return names
    except ImportError:
        pass  # pygrabber non installé
    except Exception:
        pass

    # Fallback: noms génériques
    return names


def list_available_cameras(max_cameras: int = 3, target_width: int = 1280, target_height: int = 720) -> list:
    """
    Liste les caméras disponibles sur le système.

    Args:
        max_cameras: Nombre maximum de caméras à tester
        target_width: Largeur cible pour tester les capacités
        target_height: Hauteur cible pour tester les capacités

    Returns:
        Liste de dictionnaires avec les infos de chaque caméra disponible
    """
    import os

    available = []

    # Récupérer les noms des caméras sur Windows
    camera_names_list = []
    if sys.platform == "win32":
        camera_names_list = get_camera_names_windows()

    # Sauvegarder et rediriger stderr au niveau OS
    stderr_fd = sys.stderr.fileno()
    old_stderr_fd = os.dup(stderr_fd)

    try:
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, stderr_fd)
        os.close(devnull)

        camera_index = 0
        for i in range(max_cameras):
            if sys.platform == "win32":
                cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
            else:
                cap = cv2.VideoCapture(i)

            if cap.isOpened():
                # Configurer la résolution cible pour obtenir les vraies capacités
                cap.set(cv2.CAP_PROP_FRAME_WIDTH, target_width)
                cap.set(cv2.CAP_PROP_FRAME_HEIGHT, target_height)
                cap.set(cv2.CAP_PROP_FPS, 30)

                # Lire une frame pour activer les paramètres
                cap.read()

                # Récupérer les infos réelles
                width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                backend = cap.getBackendName()

                # Utiliser le vrai nom si disponible
                if camera_index < len(camera_names_list):
                    name = camera_names_list[camera_index]
                else:
                    name = f"Camera {i}"

                available.append({
                    "id": i,
                    "name": name,
                    "resolution": f"{width}x{height}",
                    "fps": fps if fps > 0 else 30.0,
                    "backend": backend
                })
                cap.release()
                camera_index += 1
    finally:
        # Restaurer stderr
        os.dup2(old_stderr_fd, stderr_fd)
        os.close(old_stderr_fd)

    return available
