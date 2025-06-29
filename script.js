// --- Global Variables & Constants ---
const BASE_URL = 'http://localhost:5000'; // Placeholder for Python backend URL

// DOM Elements (to be cached in initializeDOM)
let drawPileElement, discardPileElement, currentPlayerHandElement,
    opponentHandElements, gameMessagesElement, colorChooserElement,
    currentTurnIndicatorElement, unoButton, passButton,
    currentWildColorIndicatorElement, drawPileCountElement,
    specialActionPromptElement;

// Player Info Area Elements (keyed by player ID/index)
const playerInfoAreas = {};
const playerHandDivs = {};
const playerCounterDivs = {};
const playerNames = {};


// Game State (client-side representation)
let clientGameState = {
    players: [], // { id: "player1", name: "Player 1", hand: [], counters: {}, isCurrentTurn: false }
    currentPlayerId: null,
    topDiscardCard: null,
    currentWildColor: null, // e.g., 'RED', 'BLUE'
    drawPileCount: 0,
    gameMessage: '',
    pendingAction: null, // e.g., { type: 'CHOOSE_COLOR', forPlayer: 'player1' }
    playDirection: 1, // 1 for forward, -1 for reverse
    gameOver: false,
    winner: null
};

// --- Initialization ---

document.addEventListener('DOMContentLoaded', () => {
    initializeDOM();
    // For now, using mock setup. Later, this will fetch from backend.
    mockGameSetup();
    // setupEventListeners(); // Will be more detailed later
});

function initializeDOM() {
    drawPileElement = document.getElementById('draw-pile');
    discardPileElement = document.getElementById('discard-pile');
    currentPlayerHandElement = document.getElementById('player-hand-current');
    gameMessagesElement = document.getElementById('game-messages');
    colorChooserElement = document.getElementById('color-chooser');
    currentTurnIndicatorElement = document.getElementById('current-turn-indicator');
    unoButton = document.getElementById('uno-button');
    passButton = document.getElementById('pass-button');
    currentWildColorIndicatorElement = document.getElementById('current-wild-color-indicator');
    drawPileCountElement = document.getElementById('draw-pile-count');
    specialActionPromptElement = document.getElementById('special-action-prompt');

    // Assuming 4 players as per HTML structure initially
    // These IDs match the HTML structure (e.g. player-1-area, player-2-hand etc.)
    // Player 1 is the human player, others are opponents
    const playerIds = ['player-1', 'player-2', 'player-3', 'player-4'];
    const opponentMapping = { // Mapping HTML areas to conceptual opponent indices
        'player-2': 'opponent-area-top', // Player 2 at the top
        'player-3': 'opponent-area-left', // Player 3 on the left
        'player-4': 'opponent-area-right' // Player 4 on the right
    };

    playerIds.forEach((id, index) => {
        playerInfoAreas[id] = document.getElementById(`${id}-area`);
        playerNames[id] = playerInfoAreas[id].querySelector('.player-name');

        if (id === 'player-1') { // Current human player
            playerHandDivs[id] = document.getElementById('player-hand-current');
        } else { // Opponents
            const opponentAreaId = opponentMapping[id];
            const opponentArea = document.getElementById(opponentAreaId);
            if (opponentArea) {
                 playerHandDivs[id] = opponentArea.querySelector('.player-hand.opponent-hand');
            } else {
                console.error(`Could not find opponent area for ${id} with mapping ${opponentAreaId}`);
            }
        }
        playerCounterDivs[id] = playerInfoAreas[id].querySelector('.player-counters');
    });

    // Event Listeners (basic for now)
    drawPileElement.addEventListener('click', handleDrawCard);
    passButton.addEventListener('click', handlePassTurn);
    unoButton.addEventListener('click', handleUnoButtonClick);

    colorChooserElement.addEventListener('click', (event) => {
        if (event.target.classList.contains('color-choice-button')) {
            const color = event.target.dataset.color;
            handleColorChoice(color);
        }
    });
}


// --- Game Setup & State Updates (Client-side, to be synced with backend) ---

// Mock function to simulate initial game setup from backend
function mockGameSetup() {
    // Simulate a 2-player game for simplicity in mock
    const player1Name = "Player 1 (You)";
    const player2Name = "Opponent 1";

    clientGameState = {
        players: [
            { id: "player-1", name: player1Name, hand: [
                { color: "RED", rank: "1", id: "R1-1" }, { color: "GREEN", rank: "7", id: "G7-1" },
                { color: "BLUE", rank: "SKIP", id: "BSK-1" }, { color: "YELLOW", rank: "0", id: "Y0-1" },
                { color: "WILD", rank: "WILD", id: "W-1" }
            ], counters: { coins: 0, shuffles: 0, lunar: 0, solar: 0, y4jail: false }, isCurrentTurn: true },
            { id: "player-2", name: player2Name, handSize: 5, counters: { coins: 0, shuffles: 0, lunar: 0, solar: 0, y4jail: false }, isCurrentTurn: false }
            // Add more players for 3 or 4 player game if HTML is set up
        ],
        currentPlayerId: "player-1",
        topDiscardCard: { color: "BLUE", rank: "5", id: "B5-1" },
        currentWildColor: null,
        drawPileCount: 80,
        gameMessage: "Game started. Player 1's turn.",
        pendingAction: null,
        playDirection: 1,
        gameOver: false,
        winner: null
    };

    // Update player names in UI
    playerNames['player-1'].textContent = player1Name;
    playerNames['player-2'].textContent = player2Name;
    if (playerNames['player-3']) playerNames['player-3'].textContent = "Opponent 2";
    if (playerNames['player-4']) playerNames['player-4'].textContent = "Opponent 3";


    // Hide unused player areas if fewer than 4 players in mock
    if (clientGameState.players.length < 3 && playerInfoAreas['player-3']) {
        playerInfoAreas['player-3'].parentElement.classList.add('hidden'); // Hides side-opponent div
    } else if (playerInfoAreas['player-3']){
         playerInfoAreas['player-3'].parentElement.classList.remove('hidden');
    }
    if (clientGameState.players.length < 4 && playerInfoAreas['player-4']) {
        playerInfoAreas['player-4'].parentElement.classList.add('hidden'); // Hides side-opponent div
    } else if (playerInfoAreas['player-4']) {
        playerInfoAreas['player-4'].parentElement.classList.remove('hidden');
    }


    updateFullUI();
}

// Main function to update the entire UI based on clientGameState
function updateFullUI() {
    // Update Player Hands
    clientGameState.players.forEach(player => {
        if (player.id === "player-1") { // Current human player
            renderPlayerHand(player.hand, playerHandDivs[player.id]);
        } else { // Opponents
            renderOpponentHand(player.handSize, playerHandDivs[player.id]);
        }
        renderPlayerCounters(player.id, player.counters);
        updatePlayerTurnIndicator(player.id, player.isCurrentTurn);
    });

    // Update Discard Pile
    renderDiscardPile(clientGameState.topDiscardCard);

    // Update Draw Pile
    drawPileCountElement.textContent = clientGameState.drawPileCount;
    drawPileElement.style.cursor = clientGameState.currentPlayerId === "player-1" && !clientGameState.pendingAction ? 'pointer' : 'default';


    // Update Game Messages
    logGameMessage(clientGameState.gameMessage, true); // true to replace existing

    // Update Current Turn Indicator (text)
    const currentPlayer = clientGameState.players.find(p => p.id === clientGameState.currentPlayerId);
    if (currentPlayer) {
        currentTurnIndicatorElement.textContent = `Turn: ${currentPlayer.name}`;
    }

    // Update Wild Color Indicator
    updateWildColorDisplay(clientGameState.currentWildColor);

    // Handle Pending Actions (e.g., show color chooser)
    if (clientGameState.pendingAction && clientGameState.pendingAction.forPlayer === "player-1") {
        if (clientGameState.pendingAction.type === 'CHOOSE_COLOR') {
            colorChooserElement.style.display = 'block';
        } else {
            colorChooserElement.style.display = 'none';
        }
        // Handle other pending actions (e.g. SWAP_CARDS) by showing specialActionPromptElement
        // This will require more complex logic for populating the prompt
         specialActionPromptElement.style.display = 'none'; // Default hide
        if (clientGameState.pendingAction.type !== 'CHOOSE_COLOR') {
            // Example: You'd populate specialActionPromptElement based on pendingAction.type
            // specialActionPromptElement.innerHTML = `<p>${clientGameState.pendingAction.message}</p> <button>Confirm</button>`;
            // specialActionPromptElement.style.display = 'block';
        }

    } else {
        colorChooserElement.style.display = 'none';
        specialActionPromptElement.style.display = 'none';
    }

    // Handle Game Over
    if (clientGameState.gameOver) {
        logGameMessage(clientGameState.winner ? `${clientGameState.winner} wins the game!` : "Game Over!", false);
        // Disable game interactions further if needed
    }
}

// --- Rendering Functions ---

function createCardDOM(cardData, isPlayerCard = true) {
    const cardDiv = document.createElement('div');
    cardDiv.classList.add('card', cardData.color); // e.g., card RED
    cardDiv.dataset.cardId = cardData.id; // Store unique card ID if available
    cardDiv.dataset.color = cardData.color;
    cardDiv.dataset.rank = cardData.rank;

    const rankDisplay = typeof cardData.rank === 'string' ? cardData.rank.replace('_', ' ') : cardData.rank;

    const rankTop = document.createElement('span');
    rankTop.classList.add('suit-symbol-top');
    rankTop.textContent = rankDisplay;

    const rankCenter = document.createElement('span');
    rankCenter.classList.add('rank');
    rankCenter.textContent = rankDisplay;

    const rankBottom = document.createElement('span');
    rankBottom.classList.add('suit-symbol-bottom');
    rankBottom.textContent = rankDisplay;

    cardDiv.appendChild(rankTop);
    cardDiv.appendChild(rankCenter);
    cardDiv.appendChild(rankBottom);

    if (isPlayerCard) {
        // Add click listener for playing the card
        cardDiv.addEventListener('click', () => handlePlayCard(cardData));
        // Highlight playable cards (logic to be added)
        // For now, let's assume a function `isCardPlayable(cardData)` exists
        if (isCardPlayable(cardData, clientGameState.topDiscardCard, clientGameState.currentWildColor)) {
            cardDiv.classList.add('playable');
        }
    }
    return cardDiv;
}

function renderPlayerHand(handArray, handElement) {
    handElement.innerHTML = ''; // Clear current hand
    handArray.forEach(card => {
        const cardDiv = createCardDOM(card, true);
        handElement.appendChild(cardDiv);
    });
}

function renderOpponentHand(handSize, handElement) {
    if (!handElement) {
        // console.warn("Attempted to render opponent hand for an element that doesn't exist.");
        return;
    }
    handElement.innerHTML = ''; // Clear current opponent hand
    for (let i = 0; i < handSize; i++) {
        const cardBackDiv = document.createElement('div');
        cardBackDiv.classList.add('card-back');
        handElement.appendChild(cardBackDiv);
    }
}

function renderDiscardPile(cardData) {
    discardPileElement.innerHTML = ''; // Clear current discard
    if (cardData) {
        const cardDiv = createCardDOM(cardData, false); // Not interactive from discard pile
        discardPileElement.appendChild(cardDiv);
    }
    updateWildColorDisplay(clientGameState.currentWildColor);
}

function renderPlayerCounters(playerId, counters) {
    const counterDiv = playerCounterDivs[playerId];
    if (!counterDiv) {
        // console.warn(`Counter div not found for player ${playerId}`);
        return;
    }

    let counterHTML = '';
    if (counters.coins > 0) counterHTML += `<span>C: ${counters.coins}</span>`;
    if (counters.shuffles > 0) counterHTML += `<span>S: ${counters.shuffles}</span>`;
    if (counters.lunar > 0) counterHTML += `<span>L: ${counters.lunar}</span>`;
    if (counters.solar > 0) counterHTML += `<span>Sol: ${counters.solar}</span>`;
    if (counters.y4jail) counterHTML += `<span>Y4J</span>`;

    counterDiv.innerHTML = counterHTML || '<span>No counters</span>';
}


function updateWildColorDisplay(color) {
    currentWildColorIndicatorElement.className = 'current-wild-color-indicator'; // Reset classes
    if (color) {
        currentWildColorIndicatorElement.classList.add(color); // e.g., RED, BLUE
    }
}

function updatePlayerTurnIndicator(playerId, isCurrentTurn) {
    const playerArea = playerInfoAreas[playerId];
    if (playerArea) {
        if (isCurrentTurn) {
            playerArea.classList.add('current-turn');
        } else {
            playerArea.classList.remove('current-turn');
        }
    }
}


function logGameMessage(message, replace = false) {
    if (!message) return;
    if (replace) {
        gameMessagesElement.innerHTML = '';
    }
    const messageP = document.createElement('p');
    messageP.textContent = message;
    gameMessagesElement.appendChild(messageP);
    gameMessagesElement.scrollTop = gameMessagesElement.scrollHeight; // Scroll to bottom
}

// --- Game Logic Stubs & Helpers (Client-side checks, to be validated by backend) ---

function isCardPlayable(cardToPlay, topDiscard, activeWildColor) {
    if (!topDiscard) return true; // Should not happen in a real game after first card

    if (cardToPlay.color === "WILD") return true; // Wilds are always playable

    if (activeWildColor) { // If a wild card is on top and a color was chosen
        return cardToPlay.color === activeWildColor;
    }
    // Standard match
    return cardToPlay.color === topDiscard.color || cardToPlay.rank === topDiscard.rank;
}


// --- Event Handlers (Stubs for now, will call backend) ---

async function handlePlayCard(cardData) {
    if (clientGameState.currentPlayerId !== "player-1" || clientGameState.pendingAction) {
        logGameMessage("Not your turn or an action is pending.", false);
        return;
    }
    if (!isCardPlayable(cardData, clientGameState.topDiscardCard, clientGameState.currentWildColor)) {
        logGameMessage("This card is not playable.", false);
        return;
    }

    logGameMessage(`Player 1 attempts to play ${cardData.color} ${cardData.rank}...`);

    // TODO: Send action to backend: { action: 'PLAY_CARD', card: cardData, chosenColor: null }
    // For now, simulate successful play
    clientGameState.topDiscardCard = cardData;
    clientGameState.players.find(p => p.id === "player-1").hand = clientGameState.players.find(p => p.id === "player-1").hand.filter(c => c.id !== cardData.id);

    if (cardData.color === "WILD") {
        clientGameState.pendingAction = { type: 'CHOOSE_COLOR', forPlayer: 'player-1' };
        logGameMessage("Played a WILD card. Choose a color.", false);
    } else {
        clientGameState.currentWildColor = null; // Reset wild color if non-wild played
        // Simulate turn change for mock
        clientGameState.players.find(p=>p.id==="player-1").isCurrentTurn = false;
        const nextPlayerIndex = (clientGameState.players.findIndex(p=>p.id===clientGameState.currentPlayerId) + 1) % clientGameState.players.length;
        clientGameState.currentPlayerId = clientGameState.players[nextPlayerIndex].id;
        clientGameState.players.find(p=>p.id===clientGameState.currentPlayerId).isCurrentTurn = true;
        logGameMessage(`${clientGameState.currentPlayerId}'s turn.`, false);

    }
    updateFullUI();
}

async function handleDrawCard() {
    if (clientGameState.currentPlayerId !== "player-1" || clientGameState.pendingAction) {
        logGameMessage("Not your turn or an action is pending.", false);
        return;
    }
    logGameMessage("Player 1 attempts to draw a card...");
    // TODO: Send action to backend: { action: 'DRAW_CARD' }
    // For now, simulate drawing a card
    if (clientGameState.drawPileCount > 0) {
        const newCard = { color: "RED", rank: "9", id: `R9-${Date.now()}`}; // Mock new card
        clientGameState.players.find(p => p.id === "player-1").hand.push(newCard);
        clientGameState.drawPileCount--;
        logGameMessage(`Player 1 drew ${newCard.color} ${newCard.rank}.`, false);
        // In real Uno, player might play the drawn card or pass.
        // For simplicity now, turn might pass or player can play this card.
    } else {
        logGameMessage("Draw pile is empty!", false);
    }
    updateFullUI();
}

async function handleColorChoice(color) {
    if (!clientGameState.pendingAction || clientGameState.pendingAction.type !== 'CHOOSE_COLOR' || clientGameState.pendingAction.forPlayer !== "player-1") {
        logGameMessage("Not awaiting color choice or not your turn to choose.", false);
        return;
    }
    logGameMessage(`Player 1 chose color: ${color}`);
    // TODO: Send action to backend: { action: 'CHOOSE_COLOR', color: color }
    clientGameState.currentWildColor = color;
    clientGameState.pendingAction = null; // Clear pending action

    // Simulate turn change for mock
    clientGameState.players.find(p=>p.id==="player-1").isCurrentTurn = false;
    const nextPlayerIndex = (clientGameState.players.findIndex(p=>p.id===clientGameState.currentPlayerId) + 1) % clientGameState.players.length;
    clientGameState.currentPlayerId = clientGameState.players[nextPlayerIndex].id;
    clientGameState.players.find(p=>p.id===clientGameState.currentPlayerId).isCurrentTurn = true;
    logGameMessage(`${clientGameState.currentPlayerId}'s turn.`, false);

    updateFullUI();
}

async function handlePassTurn() {
    if (clientGameState.currentPlayerId !== "player-1" || clientGameState.pendingAction) {
        logGameMessage("Not your turn or an action is pending.", false);
        return;
    }
    logGameMessage("Player 1 chose to pass/cannot play.");
    // TODO: Send action to backend: { action: 'PASS_TURN' }

    // Simulate turn change for mock
    clientGameState.players.find(p=>p.id==="player-1").isCurrentTurn = false;
    const nextPlayerIndex = (clientGameState.players.findIndex(p=>p.id===clientGameState.currentPlayerId) + 1) % clientGameState.players.length;
    clientGameState.currentPlayerId = clientGameState.players[nextPlayerIndex].id;
    clientGameState.players.find(p=>p.id===clientGameState.currentPlayerId).isCurrentTurn = true;
    logGameMessage(`${clientGameState.currentPlayerId}'s turn.`, false);

    updateFullUI();
}

function handleUnoButtonClick(){
    // TODO: Implement UNO call logic (send to backend, handle challenges)
    logGameMessage("Player 1 called UNO! (feature not fully implemented yet)");
}


// --- Communication with Backend (Stubs) ---
// async function fetchGameState() {
//     try {
//         const response = await fetch(`${BASE_URL}/game_state`);
//         if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
//         const data = await response.json();
//         clientGameState = data; // Assuming backend sends data in the expected format
//         updateFullUI();
//     } catch (error) {
//         console.error("Failed to fetch game state:", error);
//         logGameMessage("Error connecting to server. Using mock data.", true);
//         mockGameSetup(); // Fallback or initial setup
//     }
// }

// async function sendActionToServer(action) {
//     try {
//         const response = await fetch(`${BASE_URL}/perform_action`, {
//             method: 'POST',
//             headers: { 'Content-Type': 'application/json' },
//             body: JSON.stringify(action)
//         });
//         if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
//         const newState = await response.json();
//         clientGameState = newState;
//         updateFullUI();
//     } catch (error) {
//         console.error("Failed to send action:", error);
//         logGameMessage("Error communicating with server.", false);
//     }
// }

// Initial call to get game state (or use mock)
// fetchGameState(); // Uncomment when backend is ready
// mockGameSetup(); // For now, always start with mock for development without backend

console.log("Uno script.js loaded.");
