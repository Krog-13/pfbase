from xlsx2html import xlsx2html
from bs4 import BeautifulSoup


def convert_xlsx_html(excel_path):
    excel = xlsx2html(f"templates/{excel_path}")
    excel.seek(0)
    soup = BeautifulSoup(excel.read(), "html.parser")
    table_cells = soup.select("table tr td")
    for cell in table_cells:
        value = cell.get_text()
        if value.startswith("{"):
            type_cell = value.strip("{}")
            cell.string = ""
            new_id = cell.get("id").split("!")[1]
            if type_cell == "textarea":
                input_element = soup.new_tag("textarea", type=type_cell, id=new_id, rows=6, cols=200)
                cell.append(input_element)
            else:
                input_element = soup.new_tag("input", type=type_cell, id=new_id)
                cell.append(input_element)
    with open(f"templates/{excel_path[:-5]}.html", "w") as file:
        file.write(str(soup))


def generate_fill_html_text(path, values):
    html_path = path.split(".")[0]
    with open(f"templates/{html_path}.html", "r") as file:
        soup = BeautifulSoup(file.read(), "html.parser")
        for param in values:
            cell = soup.find("input", {"id": param["indicator__excel_cell"]})
            cell_text = soup.find("textarea", {"id": param["indicator__excel_cell"]})
            if cell:
                cell["value"] = param["indicator_value"]
            else:
                cell_text.string = param["indicator_value"]
    return str(soup)
