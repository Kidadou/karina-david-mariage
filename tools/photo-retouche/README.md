# Retouche photo — changement de fond

Remplace le fond d'un portrait (ici : intérieur de voiture) par un décor de
place de village, avec un flou d'arrière-plan type mode portrait.

## Étapes

1. Détourage du sujet avec `rembg` (modèle `birefnet-general`) :

   ```bash
   pip install pillow rembg onnxruntime
   mkdir -p work && cp <photo> work/source.jpg
   python -c "from rembg import remove,new_session;from PIL import Image;\
   img=Image.open('work/source.jpg').resize((1600,1600));\
   remove(img,session=new_session('birefnet-general'),only_mask=True).save('work/mask_birefnet-general.png')"
   ```

2. Décor de place de village (façades, clocher, platanes, terrasse, pavés),
   rendu puis fortement flouté pour simuler la faible profondeur de champ :

   ```bash
   python village_bg.py           # -> village_sharp.png
   WORKDIR=work/ python compose.py  # -> work/result.jpg
   ```

3. Variante sur le fond aquarelle du site (patio andalou) :

   ```bash
   WORKDIR=work/ BG=../../images/hero-bg.jpg python compose_aquarelle.py
   ```

Variables d'environnement : `WORKDIR` (dossier de travail), `SRC` (photo
source), `BG` (fond de la variante aquarelle).

## Résultats

- `images/photos/david-place-village.jpg` — place de village ensoleillée
- `images/photos/david-patio-aquarelle.jpg` — fond aquarelle du site
- suffixe `-1200` : versions allégées pour le web
