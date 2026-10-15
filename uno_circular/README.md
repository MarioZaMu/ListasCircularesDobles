# UNO con Listas Circulares Dobles

**Taller:** Listas Circulares Dobles aplicado en un caso de estudio
**Materia:** Estructuras de Datos · Universidad Cooperativa de Colombia · 4.º semestre
**Lenguaje:** Python 3.10+ · **Frontend:** CustomTkinter

---

## 1. Caso de estudio: los turnos en una partida de UNO

En una mesa de UNO los jugadores se sientan en círculo y el turno va pasando de uno a otro sin terminar nunca. Cuando alguien juega una **Reversa**, el turno empieza a girar en el sentido contrario. Cuando un jugador se queda sin cartas, **se levanta de la mesa** y los demás siguen jugando sin que el círculo se rompa.

Ese comportamiento es justamente el de una **lista circular doble**:

| Situación en la mesa | Operación en la lista circular doble |
|---|---|
| Cada jugador sentado | Un nodo `Player` con `prev` y `next` |
| Después del último jugador sigue el primero | `último.next == head` y `head.prev == último` |
| Sentido horario / antihorario | Avanzar por `next` (`direction = 1`) o por `prev` (`direction = -1`) |
| Carta **Reversa** | `reverse_direction()`: solo cambia `direction`, no toca los punteros |
| Carta **Salta** / **+2** / **+4** | `next_turn(skip=1)` |
| Un jugador gana (se queda sin cartas) | `remove_player(name)`: sus vecinos se enlazan entre sí |
| Agregar jugadores antes de empezar | `add_player_first` / `add_player_last` |
| No hay un "primero" real | `head` es solo una referencia; el juego avanza con `current_turn` |

## 2. ¿Por qué una lista circular doble?

### Ventajas (las vistas en clase, aplicadas al juego)
- **Recorrido en ambos sentidos:** como cada nodo tiene `prev` y `next`, la Reversa cuesta O(1). Con una lista simple habría que recorrer toda la mesa para encontrar al jugador anterior.
- **Sin fin de lista:** al ser circular no hay `None` al final, así que el turno pasa del último jugador al primero sin ningún caso especial.
- **Acceso O(1) al último:** el último jugador es `head.prev`, por eso `add_player_last` no necesita recorrer la lista.
- **Eliminar en O(1) cuando ya se tiene el nodo:** basta con `before.next = after` y `after.prev = before`. Al ganador no hay que "moverlo" de ningún arreglo.
- **Tamaño dinámico:** pueden entrar o salir jugadores sin reservar memoria fija.

### Desventajas
- **Más memoria:** cada nodo guarda dos punteros (`prev` y `next`) en lugar de uno.
- **Más punteros que actualizar:** cada inserción o eliminación modifica 4 enlaces, y si se olvida uno se rompe la invariante. Por eso existe `validate_links()`.
- **Riesgo de ciclo infinito:** como no hay `None`, los recorridos deben detenerse cuando vuelven al nodo de inicio (`if node is first: break`).
- **No hay acceso por índice:** encontrar a un jugador por su nombre cuesta O(n) (`find_player`).

## 3. Diagrama de la mesa (4 jugadores)

```
         ┌──────────────────────── Sofía.next = head ───────────────────────┐
         ▼                                                                    │
    ┌─────────┐   next   ┌─────────┐   next   ┌─────────┐   next   ┌──────────┐
    │   Tú    │ ───────▶ │   Ana   │ ───────▶ │  Luis   │ ───────▶ │  Sofía   │
    │ (head)  │ ◀─────── │         │ ◀─────── │         │ ◀─────── │ (último) │
    └─────────┘   prev   └─────────┘   prev   └─────────┘   prev   └──────────┘
         │                                                                    ▲
         └──────────────────────── head.prev = Sofía ────────────────────────┘

  Sentido horario     (direction =  1, usa next): Tú → Ana → Luis → Sofía → Tú → ...
  Sentido antihorario (direction = -1, usa prev): Tú → Sofía → Luis → Ana → Tú → ...
```

Eliminación de un nodo del medio (Ana gana y sale de la mesa):

```
  Antes:  Tú ⇄ Ana ⇄ Luis          Después:  Tú ⇄ Luis
          Tú.next = Ana                      Tú.next  = Luis   (Ana.prev.next = Ana.next)
          Luis.prev = Ana                    Luis.prev = Tú    (Ana.next.prev = Ana.prev)
```

## 4. Instalación y ejecución

Requisitos: **Python 3.10 o superior** con Tkinter (viene con el instalador oficial de Python para Windows).

```bash
cd uno_circular
python -m venv .venv
```

Windows (PowerShell o CMD):
```bash
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

Linux / macOS:
```bash
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```

Ejecutar las pruebas unitarias (desde la carpeta `uno_circular`):
```bash
python -m unittest discover -v
```

## 5. Cómo se usa

1. **Configuración:** la mesa empieza con `Tú` (humano), `Ana`, `Luis` y `Sofía`. Puedes escribir un nombre, elegir CPU o Humano y pulsar **Agregar al inicio** (`add_player_first`) o **Agregar al final** (`add_player_last`). También puedes elegir un jugador y pulsar **Eliminar jugador** (`remove_player`). Se necesitan 1 humano y entre 1 y 5 CPU.
2. **Mesa:** los jugadores se dibujan en círculo. Las flechas **verdes** son los punteros `next` y las **naranjas** son `prev`. El halo amarillo marca `current_turn` y se desliza en el sentido del juego. En el centro están la carta de arriba, el color activo y el indicador ↻ / ↺.
3. **Tu mano:** las cartas que puedes jugar aparecen resaltadas con borde blanco. Antes de jugar un comodín, elige el color en el selector. Si robas una carta jugable, puedes jugarla o pulsar **Pasar**.
4. **Panel "Estructura de datos":** muestra `head`, `head.prev`, `current_turn`, `direction`, `size` y el resultado de `validate_links()`, además de una bitácora en vivo de cada cambio de punteros. Los botones **Recorrer ↻ / ↺** recorren la mesa nodo por nodo usando los generadores.

### Reglas implementadas
- Se juega por color o por número/símbolo. Los comodines se pueden jugar siempre.
- **Salta:** el siguiente jugador pierde el turno. **Reversa:** invierte el sentido; con 2 jugadores funciona como Salta.
- **+2 / Comodín +4:** el siguiente jugador roba 2 o 4 cartas y pierde el turno (no se acumulan).
- Si no puedes jugar, robas 1 carta. Si esa carta es jugable, puedes jugarla; si no, pasa el turno.
- El primero en quedarse sin cartas sale de la mesa con `remove_player`, y la partida sigue hasta que queda un solo jugador.

## 6. Relación con las diapositivas

| Diapositivas (clase) | Este proyecto |
|---|---|
| `class Node` con `data`, `prev`, `next` | `Player` con `name`, `hand`, `is_human`, `prev`, `next` |
| `class CircularDoublyLinkedList` con `head` | `UnoTable` con `head`, `current_turn`, `direction`, `size` |
| `insert_at_beginning(data)` | `add_player_first(player)` |
| `insert_at_end(data)` | `add_player_last(player)` |
| `delete(data)` | `remove_player(name)` |
| `print_list()` | `display_table()` |
| `head.prev` es el último nodo | Igual (propiedad `last`) |

> **Corrección a `print_list`:** en las diapositivas, `print_list` usa la variable global `my_list.head` en lugar de `self.head`. Eso solo funciona si la lista se llama `my_list`. `display_table()` usa `self.head`, así que funciona con cualquier instancia (la prueba `test_display_table_uses_self_head` lo verifica con dos mesas distintas).

## 7. Explicación de cada método de `UnoTable`

| Método | Qué hace | Complejidad |
|---|---|---|
| `add_player_first(player)` | Si la lista está vacía, el nodo se apunta a sí mismo (`next = prev = player`) y pasa a ser `head`. Si no, se toma `last = head.prev` y se enlaza `player.next = head`, `player.prev = last`, `head.prev = player`, `last.next = player`; al final `head = player`. Rechaza nombres repetidos. | O(n)* |
| `add_player_last(player)` | Igual que el anterior, pero **sin mover `head`**: el nuevo nodo queda entre `last` y `head`, y por lo tanto pasa a ser el nuevo `head.prev`. | O(n)* |
| `remove_player(name)` | Busca el nodo y cubre cada caso: **lista vacía** → `None`; **no existe** → `None`; **único jugador** → `head = None`; **otro caso** → `before.next = after`, `after.prev = before`. Si era `head`, `head = after`. Si tenía el turno, `current_turn` pasa al vecino según `direction`. Limpia los punteros del nodo eliminado. | O(n) por la búsqueda, O(1) el re-enlace |
| `next_turn(skip=0)` | Avanza `1 + skip` posiciones por `next` (horario) o por `prev` (antihorario). | O(skip) |
| `peek_next(steps=1)` | Muestra quién sigue sin mover el turno (por ejemplo, la víctima de un +2). | O(steps) |
| `reverse_direction()` | `direction *= -1`. No modifica ningún puntero porque la lista ya es doble. | O(1) |
| `start_turns(player=None)` | Asigna `current_turn` (por defecto a `head`). | O(1) |
| `find_player(name)` | Recorre una vuelta con `traverse_clockwise` hasta encontrar el nombre. | O(n) |
| `traverse_clockwise(start=None)` | Generador que sigue `next` desde `head` y **se detiene al volver al inicio**. | O(n) |
| `traverse_counterclockwise(start=None)` | Generador que sigue `prev` desde `head.prev` (el último), es decir, el orden inverso. | O(n) |
| `display_table()` | Equivalente corregido de `print_list`: imprime y devuelve `Tú <-> Ana <-> ... <-> (vuelve a Tú)`. | O(n) |
| `validate_links()` | Verifica la invariante: `head.prev.next is head`, `node.next.prev is node` y `node.prev.next is node` en cada nodo, que el conteo en ambos sentidos sea igual a `size` y que `current_turn` esté en la mesa. Tiene un tope de pasos para no colgarse si la lista está rota. | O(n) |
| `is_empty()` / `__len__` | `head is None` / `size`. | O(1) |
| `__iter__` / `__contains__` | Permiten `for p in table` y `"Ana" in table`. | O(n) |

\* La inserción en sí es O(1). El O(n) se debe solo a la verificación de que el nombre no esté repetido.

Cada operación envía un mensaje al `logger` (por ejemplo, `Eliminado Ana: Tú.next → Luis, Luis.prev → Tú (nodo del medio)`), que se muestra en el panel "Estructura de datos".

> **Restricción del taller:** los jugadores **no** se guardan en `list` ni en `deque`. Solo se puede llegar a ellos desde `head` y los punteros. El mazo y las manos sí usan `list`, porque la lista circular doble se reserva para la mesa.

## 8. Estructura del proyecto

```
uno_circular/
├── main.py                 # punto de entrada
├── models/
│   ├── player.py           # Player: nodo (name, hand, is_human, prev, next)
│   ├── uno_table.py        # UnoTable: lista circular doble
│   └── card.py             # Card: color y valor
├── game/
│   ├── deck.py             # mazo de 108 cartas + pila de descarte
│   └── uno_game.py         # UnoGame: reglas e IA de los CPU
├── ui/
│   ├── app.py              # ventana principal
│   ├── setup_view.py       # pantalla de configuración
│   ├── table_view.py       # mesa (Canvas con flechas next/prev) + mano
│   └── structure_panel.py  # panel "Estructura de datos"
├── tests/
│   ├── test_uno_table.py   # pruebas de la lista circular doble
│   └── test_uno_game.py    # pruebas de reglas + partidas simuladas
├── requirements.txt
└── README.md
```

## 9. Pruebas

`tests/test_uno_table.py` cubre:
- **Lista vacía:** recorridos, eliminación, `next_turn`, `find_player` y `display_table`.
- **Inserción:** al inicio y al final, en una lista vacía (el nodo se apunta a sí mismo) y en una lista con nodos, con inserciones mezcladas y nombres duplicados.
- **Eliminación:** jugador inexistente, único jugador, `head`, último, del medio, bajar hasta 1 y luego 0, y quitar a quien tiene el turno en ambos sentidos.
- **Turnos:** vuelta completa, `skip`, reversa, `peek_next` y un solo jugador.
- **Recorridos:** ambos sentidos, desde un nodo dado y sin ciclo infinito con un solo nodo.
- **`validate_links`:** detecta `next` y `prev` rotos, `size` incorrecto, punteros `None` y un `current_turn` que no está en la mesa. También hay una prueba con **500 operaciones aleatorias** que verifica la invariante después de cada una.

`tests/test_uno_game.py` prueba las reglas (Salta, Reversa con 2 y con 3 jugadores, +2, comodín, cartas inválidas y turno incorrecto) y simula **30 partidas completas de 6 CPU**, verificando `validate_links()` en cada jugada.
