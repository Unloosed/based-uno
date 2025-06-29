# Uno Game - Frontend Documentation

This document provides a brief overview of the HTML, CSS, and JavaScript components for the Uno game's graphical user interface.

## Table of Contents
1.  [Overview](#overview)
2.  [File Structure](#file-structure)
3.  [HTML (index.html)](#html-indexhtml)
4.  [CSS (style.css)](#css-stylecss)
5.  [JavaScript (script.js)](#javascript-scriptjs)
    *   [Global Variables & State](#global-variables--state)
    *   [Initialization](#initialization)
    *   [UI Rendering Functions](#ui-rendering-functions)
    *   [Event Handlers](#event-handlers)
    *   [Backend Communication (Stubs)](#backend-communication-stubs)

## Overview

The frontend aims to provide an interactive web-based interface for playing the Uno game. It communicates with a Python backend (to be integrated) for game logic and state management. Currently, it operates using mock data for UI development and testing.

## File Structure

```
frontend/
├── index.html       # Main HTML structure for the game
├── style.css        # CSS styles for the game interface
└── script.js        # JavaScript for game logic, UI manipulation, and interaction
```
*(This README.md will also be in the frontend/ directory)*

## HTML (index.html)

The `index.html` file lays out the basic structure of the game interface. Key sections include:

*   **`game-container`**: The main wrapper for all game elements.
*   **Opponent Areas (`opponent-area-top`, `opponent-area-left`, `opponent-area-right`)**: Sections to display information about opponent players (name, card counts, counters). Each contains a `.player-info-area`.
    *   `#player-2-area`, `#player-3-area`, `#player-4-area`
*   **`middle-area`**: Contains the game table and side opponents.
*   **`game-table`**: Central area holding the draw and discard piles.
    *   **`draw-pile-area`**: Contains the draw pile (`#draw-pile`) and card count (`#draw-pile-count`).
    *   **`discard-pile-area`**: Contains the discard pile (`#discard-pile`) and an indicator for the active wild color (`#current-wild-color-indicator`).
*   **Current Player Area (`current-player-area`)**: Displays the human player's information.
    *   `#player-1-area`: Includes name (`#current-player-name`), counters, and hand (`#player-hand-current`).
*   **Game Information Area (`game-info-area`)**:
    *   `#current-turn-indicator`: Shows whose turn it is.
    *   `#game-messages`: A log for game events.
    *   `#action-buttons`: Contains buttons like "UNO!" (`#uno-button`) and "Pass Turn" (`#pass-button`).
    *   `#color-chooser`: Buttons for selecting a color after playing a Wild card (hidden by default).
    *   `#special-action-prompt`: A container for dynamic prompts related to special card actions (hidden by default).

It links to `style.css` for styling and `script.js` for functionality.

## CSS (style.css)

The `style.css` file provides the visual styling for all elements defined in `index.html`.

Key styling aspects include:

*   **Layout**: Uses Flexbox for overall page structure and component arrangement (player areas, game table).
*   **Card Appearance**: Styles for individual cards, including dimensions, colors (for Red, Yellow, Green, Blue, Wild), rank display, and hover effects. Playable cards receive a distinct highlight.
*   **Player Areas**: Styling for current player and opponent sections, including hand display and counter information. A visual highlight indicates the active player.
*   **Game Table**: Styling for draw and discard piles, including a placeholder card back image for the draw pile.
*   **Information & Action Elements**: Styles for game messages, buttons, and the color chooser.
*   **Theme**: A general "card game table" theme with green and wood-like accents.
*   **Responsiveness**: Basic provisions like `overflow-x: auto` for player hands if they contain many cards.

## JavaScript (script.js)

The `script.js` file manages the client-side game logic, DOM manipulation, and event handling.

### Global Variables & State

*   **`BASE_URL`**: Placeholder for the Python backend URL.
*   **DOM Element References**: Variables to hold cached references to frequently accessed DOM elements (e.g., `drawPileElement`, `discardPileElement`). These are populated in `initializeDOM()`.
*   **`playerInfoAreas`, `playerHandDivs`, `playerCounterDivs`, `playerNames`**: Objects to store references to player-specific UI elements, keyed by player ID.
*   **`clientGameState`**: An object representing the client's understanding of the current game state. This includes:
    *   `players`: An array of player objects (ID, name, hand/handSize, counters, isCurrentTurn).
    *   `currentPlayerId`: ID of the player whose turn it is.
    *   `topDiscardCard`: The card currently on top of the discard pile.
    *   `currentWildColor`: The active color if a Wild card effect is in play.
    *   `drawPileCount`: Number of cards left in the draw pile.
    *   `gameMessage`: General messages about game progress.
    *   `pendingAction`: Information about an action that requires player input (e.g., choosing a color).
    *   `gameOver`, `winner`: Game completion status.

### Initialization

*   **`DOMContentLoaded` Listener**: Calls `initializeDOM()` and `mockGameSetup()` (or `fetchGameState()` in a connected version) when the page is loaded.
*   **`initializeDOM()`**: Caches DOM element references and sets up initial global event listeners (for draw pile, pass button, UNO button, color chooser).
*   **`mockGameSetup()`**: Sets up `clientGameState` with initial mock data for 2 players. This is used for frontend development without a live backend. Calls `updateFullUI()` to render the mock state.

### UI Rendering Functions

These functions are responsible for updating the HTML based on `clientGameState`:

*   **`updateFullUI()`**: The main function that orchestrates UI updates by calling specific rendering functions.
*   **`createCardDOM(cardData, isPlayerCard)`**: Generates the HTML `div` for a single card, applying appropriate classes for color, rank, and playability. Adds click listeners to player cards.
*   **`renderPlayerHand(handArray, handElement)`**: Clears and re-renders the cards in the current player's hand.
*   **`renderOpponentHand(handSize, handElement)`**: Clears and re-renders opponent hands using card back representations.
*   **`renderDiscardPile(cardData)`**: Updates the card displayed on the discard pile.
*   **`renderPlayerCounters(playerId, counters)`**: Displays resource counters for a given player.
*   **`updateWildColorDisplay(color)`**: Updates the visual indicator for the chosen wild color.
*   **`updatePlayerTurnIndicator(playerId, isCurrentTurn)`**: Adds/removes a class to highlight the active player's area.
*   **`logGameMessage(message, replace)`**: Adds a message to the game log.
*   Helper functions to show/hide elements like the `colorChooserElement` or `specialActionPromptElement` based on game state.

### Event Handlers

These functions are triggered by player interactions:

*   **`handlePlayCard(cardData)`**: Called when a player clicks a card in their hand.
    *   Checks basic playability (client-side).
    *   Logs the action.
    *   (Stub) Would send a "PLAY_CARD" action to the backend.
    *   Updates mock state (moves card to discard, removes from hand, handles Wild card color choice initiation).
*   **`handleDrawCard()`**: Called when the draw pile is clicked.
    *   Logs the action.
    *   (Stub) Would send a "DRAW_CARD" action to the backend.
    *   Updates mock state (adds a card to hand, decrements draw pile count).
*   **`handleColorChoice(color)`**: Called when a color button is clicked after playing a Wild.
    *   Logs the choice.
    *   (Stub) Would send a "CHOOSE_COLOR" action to the backend.
    *   Updates mock state (sets `currentWildColor`, clears pending action, advances turn).
*   **`handlePassTurn()`**: Called when the "Pass Turn" button is clicked.
    *   Logs the action.
    *   (Stub) Would send a "PASS_TURN" action to the backend.
    *   Updates mock state (advances turn).
*   **`handleUnoButtonClick()`**: Called when the "UNO!" button is clicked. (Currently only logs).

### Backend Communication (Stubs)

*   **`fetchGameState()`** (Commented out): Intended to fetch the initial or updated game state from the backend.
*   **`sendActionToServer(action)`** (Commented out): Intended to send player actions to the backend and receive the updated game state.

The JavaScript is structured to be event-driven, updating the UI in response to player actions and (eventually) messages from the backend.
---

This documentation provides a good overview. I will now move these files into the `frontend` directory.
