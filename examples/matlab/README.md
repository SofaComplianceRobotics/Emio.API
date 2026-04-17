# TP Robotique Compliante — Python/Simulink Bridge

## Dépendances

Repose sur des modifications apportées à `emioapi/_depthcamera.py` :

- Accès aux coordonnées brutes de la caméra (ajout de la variable `trackers_camera` 
(pour le mode `"front"`, sans bruit de traitement)
- Ajout d'une fonction `process_frame()` pour séparer l'acquisition de la caméra
  du traitement des données (pour des evenements dans les process). Mais
  `update()` reste fonctionnel en appelant `process_frame()` à l'intérieur.

---

## Lancement

```bash
python main.py
```

Puis démarrer la simulation Simulink. La connexion s'établit automatiquement.

Pour arrêter : **Ctrl-C** ou appuyer sur **q** dans la fenêtre caméra.

---

## Configuration

Le seul fichier à modifier est **`params.py`** :

| Paramètre | Description |
|---|---|
| `fps` | Fréquence de la boucle (Hz) |
| `nb_markers` | Nombre de marqueurs suivis par la caméra |
| `side` | Point de vue caméra : `"top"` ou `"front"` |

Ne pas modifier les autres paramètres.

---

## Test sans robot

```bash
python test.py
```

Remplace les données caméra et moteurs par des valeurs aléatoires.
Utile pour valider le modèle Simulink seul.

---

## Structure des fichiers

| Fichier | Rôle |
|---|---|
| `main.py` | Point d'entrée |
| `params.py` | ⚙️ Configuration — **seul fichier à modifier** |
| `camera.py` | Acquisition et traitement des marqueurs |
| `process_motor.py` | Commande des moteurs |
| `simulink_bridge.py` | Communication UDP avec Simulink |
| `test.py` | Test sans matériel |
