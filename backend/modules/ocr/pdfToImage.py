# convert_pdf_to_image.py
from PIL import Image
import fitz  # PyMuPDF

def convert_pdf_first_page(pdf_path, output_image="formulaire_temoin.png", dpi=300):
    """
    Convertit la première page d'un PDF en image
    Nécessite: pip install PyMuPDF pillow
    """
    # Ouvrir le PDF
    pdf_document = fitz.open(pdf_path)
    page = pdf_document[0]  # Première page
    
    # Convertir en image avec la résolution souhaitée
    zoom = dpi / 72  # 72 DPI est la résolution par défaut de PDF
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    
    # Sauvegarder l'image
    pix.save(output_image)
    pdf_document.close()
    
    print(f"✅ PDF converti en image : {output_image}")
    print(f"   Dimensions : {pix.width} x {pix.height} pixels")
    return output_image

