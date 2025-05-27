from pydantic import BaseModel

class MilestoneConfig(BaseModel):
    id: str
    name: str
    description: str
    prerequisites: list[str]

class CurriculumConfig(BaseModel):
    name: str
    description: str
    milestones: list[MilestoneConfig]

def create_tictactoe_curriculum() -> CurriculumConfig:
    return CurriculumConfig( 
        name = "Tic-Tac-Toe Game Lesson Plan",
        description = "Build a complete tic-tac-toe game with board representation, game logic, and win conditions in a terminal game",
        milestones = [
            {
                "id": "m1",
                "name": "Board Implementation",
                "description": "Code the game board representation, board initialization with integers labelling the cells, board update, and display functions. Prefer to use a 2D array to represent the board. Display it in a 3x3 grid in terminal console.",
                "prerequisites": [],
            },
            {
                "id": "m2",
                "name": "Player Input",
                "description": "Implement functions to handle player moves. The player should be able to make a move by entering the number of the cell they want to play in.",
                "prerequisites": ["m1"],
            },
            {
                "id": "m3",
                "name": "Win Condition Implementation",
                "description": "Code the win condition checks. The game should check if the player has won by getting three in a row, column, or diagonal.",
                "prerequisites": ["m1, m2"],
            },
            {
                "id": "m4",
                "name": "Game Loop",
                "description": "Implement the main game loop. The game should alternate between the two players, and the game should continue until there is a winner or the board is full.",
                "prerequisites": ["m1", "m2", "m3"],
            },
        ],
    )