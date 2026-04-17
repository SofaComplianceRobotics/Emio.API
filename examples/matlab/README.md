# TP Robotique Compliante — Python/Simulink Bridge

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
| `fps` | Fréquence de la caméra (Hz) |
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
