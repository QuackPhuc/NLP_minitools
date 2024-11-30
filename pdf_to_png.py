import fitz  # PyMuPDF
import os
from multiprocessing import Pool, cpu_count

def convert_page_to_image(args):
    """
    Convert a single page of a PDF to an image.
    :param args: Tuple containing (pdf_path, page_index, output_folder, image_format, dpi).
    :return: None
    """
    pdf_path, page_index, output_folder, image_format, dpi = args
    try:
        pdf_document = fitz.open(pdf_path)  # Re-open the PDF in each process
        page = pdf_document.load_page(page_index)
        pix = page.get_pixmap(dpi=dpi)  # Render the page to an image
        output_path = os.path.join(output_folder, f"{page_index}.{image_format}")
        pix.save(output_path)
        pdf_document.close()
        return f"Page {page_index} saved to {output_path}"
    except Exception as e:
        return f"Error processing page {page_index}: {e}"

def pdf_to_images_parallel(pdf_path, output_folder="IMAGE", image_format="png", dpi=300):
    """
    Convert each page of a PDF into images using multiprocessing.
    :param pdf_path: Path to the PDF file.
    :param output_folder: Folder to save the images.
    :param image_format: Image format (e.g., "png", "jpg").
    :param dpi: Resolution for the output images (dots per inch).
    """
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Open the PDF to get the total page count
    pdf_document = fitz.open(pdf_path)
    total_pages = pdf_document.page_count
    pdf_document.close()

    print(f"Starting conversion of {total_pages} pages from '{pdf_path}' to images...")

    # Prepare arguments for each process
    args = [
        (pdf_path, page_index, output_folder, image_format, dpi)
        for page_index in range(total_pages)
    ]

    # Use multiprocessing Pool to process pages in parallel
    with Pool(processes=cpu_count()) as pool:
        results = pool.map(convert_page_to_image, args)

    # Log results
    for result in results:
        print(result)

    print(f"All pages have been converted and saved to '{output_folder}'.")

# Example usage
if __name__ == "__main__":
    pdf_to_images_parallel("NGULIEU.pdf", output_folder="IMAGE", image_format="png", dpi=300)
