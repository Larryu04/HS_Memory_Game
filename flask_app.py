from flask import Flask, request, render_template_string, redirect, url_for
import json
import os

app = Flask(__name__)

RARITY_ORDER = ["Common", "Rare", "Epic", "Legendary"]

SET_ORDER_DISPLAY = [
    "The Great Dark Beyond",
    "Perils in Paradise",
    "Whizbang's Workshop",
    "Into the Emerald Dream",
    "Across the Timeways",
    "The Lost City of Un'Goro",
    "Event",
    "Core"
]


def load_cards_from_file():
    if not os.path.exists("cards_data.json"): return []
    with open("cards_data.json", "r", encoding="utf-8") as f:
        return json.load(f)


@app.route("/")
def index():
    return redirect("/cards")


@app.route("/cards")
def show_cards():
    all_cards = load_cards_from_file()
    selected_rarities = request.args.getlist("rarity")
    selected_rarities = [r.capitalize() for r in selected_rarities]

    if not selected_rarities:
        selected_rarities = RARITY_ORDER

    cards_by_set = {name: [] for name in SET_ORDER_DISPLAY}

    for card in all_cards:
        if card["rarity"] in selected_rarities:
            s_name = card["set"]
            if s_name not in cards_by_set: cards_by_set[s_name] = []
            cards_by_set[s_name].append(card)

    cards_by_set = {k: v for k, v in cards_by_set.items() if v}

    html_template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hearthstone Collection Challenge</title>
        <style>
            body { background: #1e1e1e; color: #fff; font-family: 'Segoe UI', sans-serif; text-align: center; padding-bottom: 100px; overflow-x: hidden; }

            .rarity-filter { margin: 20px auto; padding: 10px 20px; background: #2c2c2c; display: inline-block; border-radius: 50px; box-shadow: 0 4px 10px rgba(0,0,0,0.5); }
            .rarity-filter label { margin: 0 10px; cursor: pointer; }
            .rarity-filter button { margin-left: 10px; padding: 5px 15px; border-radius: 20px; border: none; background: #f1c40f; font-weight: bold; cursor: pointer; }

            .grid { display: flex; flex-wrap: wrap; justify-content: center; gap: 10px; margin: 20px auto; max-width: 1400px; }

            .card { width: 120px; height: 166px; perspective: 1000px; margin: 5px; position: relative; }

            .card-inner { 
                width: 100%; height: 100%; position: relative; transform-style: preserve-3d; 
                transition: transform 1.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
            }

            .card.flip .card-inner { transform: rotateY(180deg); }

            .card-front, .card-back { position: absolute; top: 0; left: 0; width: 100%; height: 100%; backface-visibility: hidden; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.6); }
            .card-front { transform: rotateY(180deg); background: #000; }

            .card-back { 
                background-image: url("{{ url_for('static', filename='card_back.png') }}");
                background-size: cover;
                background-position: center;
                background-color: #222;
            }

            .set-title { margin-top: 50px; color: #f1c40f; text-transform: uppercase; letter-spacing: 1px; text-shadow: 0 2px 5px black; }
            .set-separator { height: 1px; background: #444; margin: 20px auto; width: 60%; }

            .guess-box { position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%); background: rgba(30, 30, 30, 0.95); padding: 10px 20px; border-radius: 50px; z-index: 1000; border: 1px solid #555; display: flex; gap: 10px; }
            .guess-box input { padding: 10px 15px; width: 250px; border-radius: 20px; border: 1px solid #444; background: #111; color: white; outline: none; }
            .guess-box button { padding: 10px 20px; border-radius: 20px; border: none; background: #28a745; color: white; font-weight: bold; cursor: pointer; }
        </style>
    </head>
    <body>
        <h1>🃏 Hearthstone Collection Challenge</h1>

        <form method="get">
            <div class="rarity-filter">
                {% for rarity in ['Common', 'Rare', 'Epic', 'Legendary'] %}
                    <label>
                        <input type="checkbox" name="rarity" value="{{ rarity }}"
                        {% if rarity in selected_rarities %} checked {% endif %}>
                        {{ rarity }}
                    </label>
                {% endfor %}
                <button type="submit">Filter</button>
            </div>
        </form>

        {% if not cards_by_set %}
            <h3 style="color: #ff6b6b;">No cards found. Run setup_cards.py again!</h3>
        {% endif %}

        {% for set_name, cards in cards_by_set.items() %}
            <div class="set-separator"></div>
            <h2 class="set-title">{{ set_name }}</h2>
            <div class="grid">
                {% for card in cards %}
                    <div class="card" data-name="{{ card.name|lower }}" data-revealed="false">
                        <div class="card-inner">
                            <img class="card-front" loading="lazy" src="{{ card.img }}">
                            <div class="card-back"></div>
                        </div>
                    </div>
                {% endfor %}
            </div>
        {% endfor %}

        <div class="guess-box">
            <input type="text" id="guess" placeholder="Type card name..." autocomplete="off"/>
            <button onclick="checkGuess()">Guess</button>
        </div>

        <script>
            function clean(str) { return str.toLowerCase().replace(/[^a-z0-9 ]/g, "").trim(); }
            const wait = (ms) => new Promise(resolve => setTimeout(resolve, ms));

            function isElementInViewport(el) {
                const rect = el.getBoundingClientRect();
                return (
                    rect.top >= 0 &&
                    rect.left >= 0 &&
                    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                );
            }

            function checkWinCondition() {
                const allCards = document.querySelectorAll(".card");
                const allRevealed = Array.from(allCards).every(card => card.dataset.revealed === "true");

                if (allRevealed) {
                    setTimeout(() => {
                        alert("🎉 Well done! You guessed all cards!");
                    }, 1000);
                }
            }
            // ---------------------------------------------

            async function checkGuess() {
                const input = document.getElementById("guess");
                const guess = clean(input.value);
                if (!guess) return;

                const cards = document.querySelectorAll(".card");
                let found = false;

                for (const div of cards) {
                    if (div.dataset.revealed === "true") continue;

                    if (clean(div.dataset.name) === guess) {

                        if (isElementInViewport(div)) {
                            await wait(100); 
                            div.classList.add("flip");
                        } else {
                            div.scrollIntoView({ behavior: "smooth", block: "center", inline: "center" });
                            await wait(1300); 
                            div.classList.add("flip");
                        }

                        div.dataset.revealed = "true";
                        found = true;

                        checkWinCondition(); 

                        await wait(200);
                    }
                }

                if (found) {
                    input.value = "";
                    input.style.borderColor = "#28a745";
                } else {
                    input.style.borderColor = "#dc3545";
                }
                setTimeout(() => input.style.borderColor = "#444", 1000);
                input.focus();
            }

            document.getElementById("guess").addEventListener("keydown", function (e) {
                if (e.key === "Enter") {
                    e.preventDefault();
                    checkGuess();
                }
            });
        </script>
    </body>
    </html>
    """

    return render_template_string(
        html_template,
        cards_by_set=cards_by_set,
        selected_rarities=selected_rarities
    )


if __name__ == "__main__":
    app.run(debug=True)