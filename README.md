# Fichess

Fichess is an AI chess engine built as a project for an Artifical Intelligence course. 

It is built around a minimax algorithm with alpha-beta pruning, move ordering and search optimizations, as well as custom heuristics for evaluating each state. 

The engine also has a GUI built with Pygame, allowing users to play against the bot in a user-friendly interface.

## Installation

To set up the project locally,
1. **Clone this repository**:
```bash
git clone https://github.com/gavro081/fichess.git
cd fichess
```

2. **(Optional)** Create and activate a virtual environment.

3. **Install dependencies**: `pip install -r requirements.txt`

4. **Run the GUI**: `python3 main.py`

## Testing
You can test the engine by playing against it in the GUI. If you want to modify the heuristics, or add new ones, 
you can do that in `Eval.py`. Some unit tests are written in `/tests` to ensure all functions are 
working properly. 


## UCI Support
Fichess is [UCI](https://www.chessprogramming.org/UCI) compliant, meaning it can communicate with other engines and interfaces using the Universal Chess Interface protocol.
You can test Fichess against other engines using UCI-compatible tools such as [Cute Chess](https://github.com/cutechess/cutechess), either via CLI or GUI. 
To run, call the uci.py function and let the tools handle the rest.

