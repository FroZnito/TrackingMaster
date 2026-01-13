# TrackingMaster - Roadmap de Développement

Un projet de tracking complet utilisant la vision par ordinateur et l'intelligence artificielle.

---

## Version 0.1 - Foundation ✅
**Objectif** : Mise en place du projet et accès caméra

### Features
- [x] Initialisation du projet (structure, dépendances)
- [x] Accès au flux vidéo de la webcam
- [x] Affichage du flux en temps réel dans une fenêtre
- [x] Contrôles basiques (pause, quitter, screenshot)
- [x] Gestion des erreurs caméra

### Technologies
- Python 3.10+
- OpenCV

---

## Version 0.2 - Hand Detection ✅
**Objectif** : Détecter la présence des mains dans le flux vidéo

### Features
- [x] Intégration de MediaPipe Hands
- [x] Détection des mains (gauche/droite)
- [x] Affichage des landmarks (21 points par main)
- [x] Affichage des connexions entre les points
- [x] Compteur de mains détectées

### Technologies
- MediaPipe

---

## Version 0.3 - Finger Tracking ✅
**Objectif** : Tracking précis des doigts et reconnaissance de gestes basiques

### Features
- [x] Identification de chaque doigt (pouce, index, majeur, annulaire, auriculaire)
- [x] Détection doigt levé / baissé avec multi-critères (5 critères, 3+ requis)
- [x] Comptage universel des doigts (n'importe quels doigts = compte)
- [x] Reconnaissance de 17 gestes (fist, open_hand, thumbs_up, thumbs_down, peace, two, pointing, ok, rock, three, four, gun, call_me, loser, pinky_up, thumb_index_pinky)
- [x] Différenciation Peace (V écarté) vs Two (doigts serrés) via angle de spread
- [x] Affichage visuel de l'état de chaque doigt avec indicateurs de confiance
- [x] Mode debug avec seuils ajustables en temps réel (curl, thumb_curl, spread)
- [x] Score de confiance par doigt (0-5 critères validés)
- [x] Export des données en JSON et CSV (dossier `data/`)
- [x] Fenêtre d'aide avec toutes les commandes [?]

### Performance
- [x] Threading : MediaPipe en arrière-plan (~30 FPS), rendu principal (~60 FPS)
- [x] Single-pass overlay rendering (3-5x plus rapide)
- [x] Toggle threading avec touche [T]

### Technologies
- Module FingerTracker avec analyse multi-critères des landmarks
- Module ThreadedTracker pour traitement asynchrone
- Module OverlayRenderer pour rendu optimisé
- Système de thème UI moderne (classe Theme)

---

## Version 0.4 - Face Detection
**Objectif** : Détecter et tracker le visage

### Features
- [ ] Intégration de MediaPipe Face Mesh
- [ ] Détection du visage (468 landmarks)
- [ ] Tracking de la position du visage
- [ ] Bounding box autour du visage
- [ ] Détection de plusieurs visages

---

## Version 0.5 - Head Pose Estimation
**Objectif** : Estimer l'orientation de la tête en 3D

### Features
- [ ] Calcul des angles de rotation (pitch, yaw, roll)
- [ ] Visualisation de l'orientation avec axes 3D
- [ ] Détection : tête tournée gauche/droite, haut/bas
- [ ] Indicateur visuel de la direction du regard
- [ ] Historique des mouvements de tête

---

## Version 0.6 - Facial Expressions
**Objectif** : Reconnaître les expressions faciales

### Features
- [ ] Détection des yeux ouverts/fermés (blink detection)
- [ ] Détection du sourire
- [ ] Détection sourcils levés/froncés
- [ ] Détection bouche ouverte/fermée
- [ ] Classification des émotions : neutre, joie, surprise, colère, tristesse
- [ ] Affichage du niveau de confiance pour chaque émotion

---

## Version 0.7 - Eye Tracking
**Objectif** : Tracker le regard et les mouvements oculaires

### Features
- [ ] Détection des pupilles
- [ ] Direction du regard (gauche, droite, centre, haut, bas)
- [ ] Heatmap des zones regardées
- [ ] Détection de fatigue oculaire
- [ ] Compteur de clignements par minute

---

## Version 0.8 - Body Pose (Upper Body)
**Objectif** : Tracker le haut du corps

### Features
- [ ] Intégration de MediaPipe Pose
- [ ] Détection épaules, coudes, poignets
- [ ] Estimation de la posture (droit, penché)
- [ ] Détection des bras levés/croisés
- [ ] Alerte de mauvaise posture

---

## Version 0.9 - Unified Tracking
**Objectif** : Combiner tous les trackings en un système unifié

### Features
- [ ] Fusion mains + visage + corps en temps réel
- [ ] Optimisation des performances (FPS)
- [ ] Mode debug avec toutes les informations
- [ ] Mode clean avec overlay minimaliste
- [ ] Export des données de tracking en JSON

---

## Version 1.0 - Activity Recognition
**Objectif** : Reconnaître les activités de l'utilisateur

### Features
- [ ] Détection : travail sur ordinateur, téléphone, lecture, repos
- [ ] Reconnaissance de gestes complexes (salut, applaudissement)
- [ ] Détection de présence/absence
- [ ] Historique des activités avec timestamps
- [ ] Statistiques d'utilisation

---

## Version 1.1 - Dashboard & Analytics
**Objectif** : Interface utilisateur et visualisation des données

### Features
- [ ] Interface web avec Flask/FastAPI
- [ ] Dashboard temps réel
- [ ] Graphiques d'activité
- [ ] Export des rapports (PDF, CSV)
- [ ] Configuration via interface web

---

## Version 1.2 - API & Integration
**Objectif** : Exposer les fonctionnalités via API

### Features
- [ ] API REST pour accéder aux données de tracking
- [ ] WebSocket pour le streaming temps réel
- [ ] Documentation Swagger/OpenAPI
- [ ] SDK Python pour intégration facile
- [ ] Exemples d'intégration

---

## Version 1.3 - AI Assistant Integration
**Objectif** : Intégrer une IA conversationnelle

### Features
- [ ] Intégration LLM (OpenAI API / Ollama local)
- [ ] Commandes vocales pour contrôler le tracking
- [ ] L'IA décrit ce qu'elle voit en temps réel
- [ ] Conversation contextuelle basée sur l'activité détectée
- [ ] Suggestions intelligentes basées sur le comportement

---

## Version 1.4 - Voice & Audio
**Objectif** : Ajouter les capacités audio

### Features
- [ ] Reconnaissance vocale (speech-to-text)
- [ ] Synthèse vocale (text-to-speech)
- [ ] Commandes vocales pour l'application
- [ ] Détection du niveau sonore ambiant
- [ ] Transcription en temps réel

---

## Version 1.5 - Smart Automation
**Objectif** : Automatisations basées sur le tracking

### Features
- [ ] Règles personnalisables (si geste X, alors action Y)
- [ ] Intégration avec le système (notifications, apps)
- [ ] Contrôle de la souris par gestes
- [ ] Raccourcis personnalisés par gestes
- [ ] Mode gaming : mapping gestes vers touches

---

## Version 2.0 - TrackingMaster Pro
**Objectif** : Version complète et optimisée

### Features
- [ ] Interface desktop native (Electron/Tauri)
- [ ] Support multi-caméras
- [ ] Mode performance (GPU acceleration)
- [ ] Plugins system
- [ ] Thèmes personnalisables
- [ ] Documentation complète
- [ ] Tests unitaires et d'intégration

---

## Stack Technique Globale

| Catégorie | Technologies |
|-----------|--------------|
| Language | Python 3.10+ |
| Vision | OpenCV, MediaPipe |
| ML/AI | TensorFlow, PyTorch, scikit-learn |
| LLM | OpenAI API, Ollama, LangChain |
| Web | FastAPI, Flask, WebSocket |
| Frontend | React, TailwindCSS |
| Desktop | Electron, Tauri |
| Audio | SpeechRecognition, pyttsx3 |

---

## Comment Contribuer

Chaque version sera développée dans une branche dédiée (`v0.1`, `v0.2`, etc.) puis mergée dans `main` une fois complète.

---

*Projet initié le 12 janvier 2026*
