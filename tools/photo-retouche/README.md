# Retouche photo — changement de fond

Remplace le fond d'un portrait (ici : intérieur de voiture) par un fond
d'extérieur très flou, façon photo prise en mode portrait (faible profondeur
de champ). Le décor n'est volontairement pas identifiable : ce sont des masses
de couleur (pierre chaude, feuillage, ombre au sol) floutées et des disques de
bokeh, ce qui donne un rendu photographique plutôt qu'illustré.

## Utilisation

```bash
pip install pillow rembg onnxruntime
mkdir -p work && cp <photo> work/source.jpg

# 1. détourage du sujet (modèle birefnet-general)
python -c "from rembg import remove,new_session;from PIL import Image;\
img=Image.open('work/source.jpg').resize((1600,1600));\
remove(img,session=new_session('birefnet-general'),only_mask=True).save('work/mask_birefnet-general.png')"

# 2. fond flou + compositing
WORKDIR=work/ python compose_bokeh.py    # -> work/result_bokeh.jpg
```

Variables d'environnement : `WORKDIR` (dossier de travail), `SRC` (photo source).

Le compositing fait : retrait du liseré de bord, raccord de lumière (le sujet
est réchauffé, un halo clair déborde du fond sur ses contours) et grain commun
aux deux couches pour unifier le montage.

## Résultat

- `images/photos/david-portrait-exterieur.jpg` (3340×3340)
- `images/photos/david-portrait-exterieur-1200.jpg` (version web)
