"""Генерация UML-диаграмм классов в формате Graphviz."""
import html, subprocess

FONT = "DejaVu Sans"

def cls(name, attrs=(), methods=(), kind="", fill="#FFFFFF"):
    """HTML-метка узла в виде UML-класса с тремя секциями."""
    rows = []
    title = html.escape(name)
    if kind == "abstract":
        title = f"<I>{title}</I>"
    elif kind == "enum":
        title = f"«enumeration»<BR/>{title}"
    rows.append(f'<TR><TD BGCOLOR="{fill}"><B>{title}</B></TD></TR>')
    def sect(items):
        if not items:
            return '<TR><TD ALIGN="LEFT" HEIGHT="6"> </TD></TR>'
        body = "<BR ALIGN=\"LEFT\"/>".join(html.escape(i) for i in items)
        return f'<TR><TD ALIGN="LEFT">{body}<BR ALIGN="LEFT"/></TD></TR>'
    rows.append(sect(attrs)); rows.append(sect(methods))
    return ('<<TABLE BORDER="1" CELLBORDER="0" CELLSPACING="0" '
            'CELLPADDING="3">' + "".join(rows) + "</TABLE>>")

def node(name, *a, **k):
    ident = k.pop("ident", name.replace("<", "_").replace(">", ""))
    return f'  {ident} [label={cls(name, *a, **k)}];\n'

HEAD = f'''digraph G {{
  graph [rankdir=BT, nodesep=0.35, ranksep=0.55, dpi=170, splines=ortho,
         fontname="{FONT}"];
  node [shape=plaintext, fontname="{FONT}", fontsize=9];
  edge [fontname="{FONT}", fontsize=8];
'''
INH = 'arrowhead=empty'
ASSOC = 'arrowhead=vee'
COMP = 'arrowhead=none, arrowtail=diamond, dir=both'

# ------------------------------------------------------------ диаграмма 1
d = HEAD
d += node("Entity", ["- _id: int"], ["+ id: int", "+ to_dict(): dict",
          "+ from_dict(data): Entity"], kind="abstract", fill="#E8EEF7")
d += node("Accessory", ["- _name: str"], ["+ name: str"])
d += node("Station", ["- _name: str", "- _address: str"], [])
d += node("Customer", ["- _full_name: str", "- _email: str",
          "- _birth_date: date"], ["+ age_on(day): int"])
d += node("Bike", ["- _model: str", "- _price_per_hour: float",
          "+ station_id: int", "+ accessory_ids: list[int]",
          "+ KIND, MAX_HOURS, MIN_AGE,", "   REQUIRES_APPROVAL"],
          ["+ initial_status(): RentalStatus",
           "+ calculate_cost(slot): float",
           "+ check_rental(slot, customer)"], kind="abstract",
          fill="#E8EEF7")
d += node("CityBike", ["KIND = 'city'", "MAX_HOURS = 24", "MIN_AGE = 12"], [])
d += node("ElectricBike", ["KIND = 'electric'", "MAX_HOURS = 8",
          "MIN_AGE = 16", "REQUIRES_APPROVAL = True",
          "+ battery_wh: int"], [])
d += node("Rental", ["+ bike_id: int", "+ customer_id: int",
          "+ slot: TimeSlot", "+ cost: float",
          "- _status: RentalStatus"],
          ["+ confirm()", "+ cancel()", "+ is_active: bool"])
d += node("TimeSlot", ["- _start: datetime", "- _end: datetime"],
          ["+ duration_hours: float", "+ overlaps(other): bool"])
d += node("RentalStatus", ["PENDING", "CONFIRMED", "CANCELLED"], [],
          kind="enum")
d += node("Notification", ["+ recipient_email: str", "+ text: str",
          "+ created_at: datetime"], [])
d += node("Repository<T>", ["- _items: dict[int, T]"],
          ["+ next_id(): int", "+ add(item): T", "+ get(id): T",
           "+ all(): list[T]", "+ find(predicate): list[T]",
           "+ update(item): T", "+ delete(id): T"], ident="Repository")
d += node("RentalService", ["+ stations, accessories, bikes,",
          "   customers, rentals:", "   Repository[...]",
          "+ notifications: list[Notification]"],
          ["+ create_rental(...): Rental",
           "+ reschedule_rental(...)", "+ approve_rental(id)",
           "+ cancel_rental(id)", "+ find_free_bikes(...)",
           "+ move_bike(id, station_id)",
           "+ delete_bike(id) / delete_customer(id)",
           "+ export_data() / import_data(data)"], fill="#FFF6DD")
d += node("Storage", ["+ path: Path"],
          ["+ save(service)", "+ load(service)", "# _write(data)",
           "# _read(): dict"], kind="abstract", fill="#E8EEF7")
d += node("JsonStorage", [], ["# _write(data)", "# _read(): dict"])
d += node("XmlStorage", [], ["# _write(data)", "# _read(): dict"])
d += node("ConsoleApp", ["- service: RentalService"],
          ["+ run()", "+ create_rental() ...", "+ save_data()",
           "+ load_data()"], fill="#E7F5E8")
for c in ["Accessory", "Station", "Customer", "Bike", "Rental"]:
    d += f"  {c} -> Entity [{INH}];\n"
d += f"  CityBike -> Bike [{INH}];\n  ElectricBike -> Bike [{INH}];\n"
d += f"  JsonStorage -> Storage [{INH}];\n  XmlStorage -> Storage [{INH}];\n"
d += f"  Repository -> Entity [{ASSOC}, style=dashed, label=\"T\"];\n"
d += f"  Rental -> TimeSlot [{COMP}];\n"
d += f"  Rental -> RentalStatus [{ASSOC}];\n"
d += f"  Rental -> Bike [{ASSOC}, label=\"bike_id\"];\n"
d += f"  Rental -> Customer [{ASSOC}, label=\"customer_id\"];\n"
d += f"  Bike -> Station [{ASSOC}];\n  Bike -> Accessory [{ASSOC}, label=\"0..*\"];\n"
d += f"  RentalService -> Repository [{COMP}, label=\"5\"];\n"
d += f"  RentalService -> Notification [{COMP}, label=\"0..*\"];\n"
d += f"  Storage -> RentalService [{ASSOC}, style=dashed];\n"
d += f"  ConsoleApp -> RentalService [{ASSOC}];\n"
d += f"  ConsoleApp -> Storage [{ASSOC}, style=dashed];\n"
d += "}\n"
open("class1.dot", "w", encoding="utf-8").write(d)
subprocess.run(["dot", "-Tpng", "class1.dot", "-o", "class1.png"], check=True)

# ------------------------------------------------------------ диаграмма 2
d = HEAD.replace("splines=ortho", "splines=true")
d += node("Exception", [], [], fill="#EEEEEE")
d += node("BikeRentalError", [], [], fill="#FBE3E3")
d += node("ValidationError", [], [], fill="#FBE3E3")
d += node("EntityNotFoundError", ["+ entity_name: str", "+ entity_id: int"],
          [], fill="#FBE3E3")
d += node("DuplicateEntityError", [], [], fill="#FBE3E3")
d += node("DependencyError", [], [], fill="#FBE3E3")
d += node("RentalConflictError", ["+ bike_model: str",
          "+ conflict_rental_id: int"], [], fill="#FBE3E3")
d += node("AgeRestrictionError", [], [], fill="#FBE3E3")
d += node("InvalidStatusError", [], [], fill="#FBE3E3")
d += node("StorageError", [], [], fill="#FBE3E3")
for c in ["Bike", "Rental", "Repository", "RentalService", "Storage",
          "Customer", "TimeSlot"]:
    d += f'  {c} [label={cls(c, fill="#E8EEF7")}];\n'
d += f"  BikeRentalError -> Exception [{INH}];\n"
for c in ["ValidationError", "EntityNotFoundError", "DuplicateEntityError",
          "DependencyError", "RentalConflictError", "AgeRestrictionError",
          "InvalidStatusError", "StorageError"]:
    d += f"  {c} -> BikeRentalError [{INH}];\n"
R = 'style=dashed, arrowhead=vee, label="«raises»"'
d += f"  Bike -> AgeRestrictionError [{R}];\n"
d += f"  Bike -> ValidationError [{R}];\n"
d += f"  Customer -> ValidationError [{R}];\n"
d += f"  TimeSlot -> ValidationError [{R}];\n"
d += f"  Rental -> InvalidStatusError [{R}];\n"
d += f"  Repository -> EntityNotFoundError [{R}];\n"
d += f"  Repository -> DuplicateEntityError [{R}];\n"
d += f"  RentalService -> RentalConflictError [{R}];\n"
d += f"  RentalService -> DependencyError [{R}];\n"
d += f"  Storage -> StorageError [{R}];\n"
d += "}\n"
open("class2.dot", "w", encoding="utf-8").write(d)
subprocess.run(["dot", "-Tpng", "class2.dot", "-o", "class2.png"], check=True)
print("ok")
