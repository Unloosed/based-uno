// --- Global Variables and Constants ---
const API_BASE_URL = "/api"; // Assuming Flask serves API at /api
let मानव_खिलाड़ी_का_नाम = "Player 1"; // Default, can be updated if needed
let वर्तमान_खेल_की_स्थिति = null;
let चयनित_कार्ड_का_सूचकांक = null; // Index of the card selected in the hand

// --- DOM Elements ---
// (Get references to all necessary DOM elements after the DOM is loaded)
let opponentsArea, topCardEl, currentWildColorEl, currentPlayerEl, playDirectionEl;
let handCardsContainer, humanPlayerNameEl;
let playCardButton, drawCardButton, cpuTurnButton;
let pendingActionInputArea, standardActionsArea, cpuTurnArea;
let messageLogEl;

document.addEventListener('DOMContentLoaded', () => {
    // Initialize DOM element references
    opponentsArea = document.getElementById('opponents-area');
    topCardEl = document.getElementById('top-card').querySelector('span');
    currentWildColorEl = document.getElementById('current-wild-color').querySelector('span');
    currentPlayerEl = document.getElementById('current-player').querySelector('span');
    playDirectionEl = document.getElementById('play-direction').querySelector('span');

    handCardsContainer = document.getElementById('hand-cards');
    humanPlayerNameEl = document.getElementById('human-player-name');

    playCardButton = document.getElementById('button-play-card');
    drawCardButton = document.getElementById('button-draw-card');
    cpuTurnButton = document.getElementById('button-cpu-turn');

    standardActionsArea = document.getElementById('standard-actions');
    pendingActionInputArea = document.getElementById('pending-action-input-area');
    cpuTurnArea = document.getElementById('cpu-turn-area');

    messageLogEl = document.getElementById('message-log');

    // Attach initial event listeners
    playCardButton.addEventListener('click', handlePlayCard);
    drawCardButton.addEventListener('click', handleDrawCard);
    cpuTurnButton.addEventListener('click', handleCpuTurn); // Will need API endpoint

    // Load initial game state
    initGame();
});

// --- API Helper Functions ---
async function fetchFromAPI(endpoint, method = 'GET', body = null) {
    const options = {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
    };
    if (body) {
        options.body = JSON.stringify(body);
    }
    try {
        const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
        }
        return await response.json();
    } catch (error) {
        console.error(`Error fetching from API endpoint ${endpoint}:`, error);
        logMessage(`Error: ${error.message}`, 'error');
        // If game state is available in error, update UI with it.
        if (error.game_state) {
            वर्तमान_खेल_की_स्थिति = error.game_state;
            renderAll();
        }
        throw error; // Re-throw to be caught by calling function if needed
    }
}

async function getGameState() {
    return fetchFromAPI("/game_state");
}

async function playCardAPI(playerName, cardIndex, chosenColor = null) {
    const body = {
        player_name: playerName,
        card_index: cardIndex,
    };
    if (chosenColor) {
        body.chosen_color = chosenColor; // e.g., "RED", "BLUE"
    }
    return fetchFromAPI("/play_card", 'POST', body);
}

async function drawCardAPI(playerName) {
    return fetchFromAPI("/draw_card", 'POST', { player_name: playerName });
}

async function provideActionInputAPI(playerName, actionInput) {
    return fetchFromAPI("/provide_action_input", 'POST', { player_name: playerName, action_input: actionInput });
}

// (Placeholder for CPU turn API - to be defined in plan step 7)
async function cpuPlayTurnAPI(playerName) {
    logMessage(`Attempting to simulate turn for CPU: ${playerName}... (Endpoint not yet implemented)`);
    // This will require a new backend endpoint, e.g., /api/cpu_play_turn
    // For now, let's just refresh state. User would click again if it was a real CPU.
    // Or, if backend automatically processes CPU turns after a human move, this might not be strictly needed
    // in this exact form.
    // await new Promise(resolve => setTimeout(resolve, 500)); // Simulate delay
    // return getGameState();
    alert("CPU turn simulation endpoint is not yet implemented in the backend.");
    return वर्तमान_खेल_की_स्थिति ? { game_state: वर्तमान_खेल_की_स्थिति, message:"Manual refresh recommended or implement CPU endpoint."} : getGameState();
}


// --- Rendering Functions ---
function renderOpponents(players) {
    opponentsArea.innerHTML = '<h2>Opponents</h2>'; // Clear previous
    players.forEach(player => {
        if (player.name !== मानव_खिलाड़ी_का_नाम) {
            const opponentDiv = document.createElement('div');
            opponentDiv.className = 'opponent';
            opponentDiv.id = `opponent-${player.name.replace(/\s+/g, '-')}`;

            let text = `${player.name}: ${player.card_count} card(s)`;
            const counters = [];
            if (player.coins > 0) counters.push(`C:${player.coins}`);
            if (player.shuffle_counters > 0) counters.push(`S:${player.shuffle_counters}`);
            if (player.lunar_mana > 0) counters.push(`L:${player.lunar_mana}`);
            if (player.solar_mana > 0) counters.push(`Sol:${player.solar_mana}`);
            if (player.has_get_out_of_jail_card) counters.push("Y4Jail");
            if (counters.length > 0) text += ` (${counters.join(', ')})`;

            opponentDiv.textContent = text;
            opponentsArea.appendChild(opponentDiv);
        }
    });
}

function renderGameStatus(gameState) {
    topCardEl.textContent = gameState.top_card ? gameState.top_card.display_str : 'N/A';
    if (gameState.top_card && gameState.top_card.color === 'WILD' && gameState.current_wild_color) {
        currentWildColorEl.textContent = gameState.current_wild_color;
        currentWildColorEl.parentElement.style.display = 'block';
    } else {
        currentWildColorEl.textContent = 'N/A';
        currentWildColorEl.parentElement.style.display = 'none';
    }
    currentPlayerEl.textContent = gameState.current_player_name;
    playDirectionEl.textContent = gameState.play_direction;
    humanPlayerNameEl.textContent = मानव_खिलाड़ी_का_नाम; // In case it could change
}

function renderPlayerHand(hand) { // hand is an array of card objects from game_state.player.hand
    handCardsContainer.innerHTML = ''; // Clear previous cards
    चयनित_कार्ड_का_सूचकांक = null;
    playCardButton.disabled = true;

    if (!hand || hand.length === 0) {
        const noCardsMsg = document.createElement('p');
        noCardsMsg.textContent = "Your hand is empty.";
        handCardsContainer.appendChild(noCardsMsg);
        return;
    }

    hand.forEach((card, index) => {
        const cardDiv = document.createElement('div');
        cardDiv.className = 'card';
        // Add color specific classes for styling potential
        if (card.color) cardDiv.classList.add(card.color); // Assumes card.color is "RED", "BLUE" etc.
        if (card.rank === "WILD" || card.rank === "WILD_DRAW_FOUR") cardDiv.classList.add("WILD");


        cardDiv.textContent = card.display_str; // Using display_str from card.to_dict()
        cardDiv.dataset.cardIndex = index; // Store index for easy retrieval

        cardDiv.addEventListener('click', () => {
            if (चयनित_कार्ड_का_सूचकांक !== null) {
                const prevSelected = handCardsContainer.querySelector(`[data-card-index="${चयनित_कार्ड_का_सूचकांक}"]`);
                if (prevSelected) prevSelected.classList.remove('selected');
            }
            चयनित_कार्ड_का_सूचकांक = index;
            cardDiv.classList.add('selected');
            playCardButton.disabled = false; // Enable play button
        });
        handCardsContainer.appendChild(cardDiv);
    });
}

function logMessage(message, type = 'info') { // type can be 'info', 'error', 'success'
    const messageP = document.createElement('p');
    messageP.textContent = message;
    messageP.className = type; // For potential styling
    messageLogEl.appendChild(messageP);
    messageLogEl.scrollTop = messageLogEl.scrollHeight; // Scroll to bottom
}

function renderPendingActionUI(pendingActionType, actionData, gameState) {
    pendingActionInputArea.innerHTML = ''; // Clear previous inputs
    standardActionsArea.style.display = 'none'; // Hide standard play/draw

    if (!pendingActionType) {
        standardActionsArea.style.display = 'flex'; // Or 'block' based on your CSS for the container
         // Check if it's human player's turn to enable/disable standard actions
        if (gameState.current_player_name === मानव_खिलाड़ी_का_नाम) {
            drawCardButton.disabled = false;
            playCardButton.disabled = (चयनित_कार्ड_का_सूचकांक === null);
        } else {
            drawCardButton.disabled = true;
            playCardButton.disabled = true;
        }
        return;
    }

    // Ensure action buttons are disabled if a pending action is for another player
    // or if the human player is not the actor for the current pending action.
    let isHumanPlayerActor = false;
    // Determine if human player is the actor for this pending action
    // This logic needs to be robust based on how actionData identifies the actor
    if (pendingActionType === "CHOOSE_COLOR") {
        // Actor is player_idx in actionData if not for Rank 6, or original_player_idx if for Rank 6
        const actorIdx = actionData.is_for_rank_6_wild ? actionData.original_player_idx : actionData.player_idx;
        if (gameState.players[actorIdx] && gameState.players[actorIdx].name === मानव_खिलाड़ी_का_नाम) {
            isHumanPlayerActor = true;
        }
    } else if (pendingActionType === "SWAP_CARD_RIGHT" || pendingActionType === "SWAP_CARD_ANY" || pendingActionType === "PLAY_ANY_AND_DRAW_ONE") {
        if (gameState.players[actionData.original_player_idx] && gameState.players[actionData.original_player_idx].name === मानव_खिलाड़ी_का_नाम) {
            isHumanPlayerActor = true;
        }
    } else if (pendingActionType === "DISCARD_FROM_PLAYER_HAND") {
         if (gameState.players[actionData.chooser_idx] && gameState.players[actionData.chooser_idx].name === मानव_खिलाड़ी_का_नाम) {
            isHumanPlayerActor = true;
        }
    }


    if (!isHumanPlayerActor) {
        logMessage(`Waiting for ${gameState.players[actionData.original_player_idx || actionData.player_idx || actionData.chooser_idx].name} to resolve ${pendingActionType}...`);
        // Optionally show a disabled state or message
        pendingActionInputArea.innerHTML = `<p>Waiting for another player to act on: ${pendingActionType}</p>`;
        return;
    }


    const promptLabel = document.createElement('label');
    pendingActionInputArea.appendChild(promptLabel);

    if (pendingActionType === "CHOOSE_COLOR") {
        promptLabel.textContent = "Choose a color for the Wild card:";
        const colors = ["RED", "YELLOW", "GREEN", "BLUE"];
        colors.forEach(color => {
            const button = document.createElement('button');
            button.textContent = color;
            button.className = `color-choice-button ${color}`; // For styling
            button.addEventListener('click', async () => {
                try {
                    const result = await provideActionInputAPI(मानव_खिलाड़ी_का_नाम, { chosen_color: color });
                    logMessage(result.message);
                    वर्तमान_खेल_की_स्थिति = result.game_state;
                    renderAll();
                } catch (error) {
                    // Error already logged by fetchFromAPI
                }
            });
            pendingActionInputArea.appendChild(button);
        });
    } else if (pendingActionType === "SWAP_CARD_RIGHT" || pendingActionType === "SWAP_CARD_ANY") {
        // This is complex and will require more detailed UI elements
        // For now, a placeholder:
        promptLabel.textContent = `Provide input for ${pendingActionType}. (UI for this is complex and pending full implementation). Card to give (select from hand), then target player (for ANY), then card to take.`;

        // Simplified: Ask for indices via prompt for now, or build proper selectors
        const cardToGiveIdx = selected_card_index; // Assume card is already selected from hand for "Play"
        if (cardToGiveIdx === null) {
            logMessage("Please select a card from your hand to give for the swap first.", "error");
            // Re-enable standard actions to allow card selection, then player must re-initiate the "play" of the swap card.
            // This flow is tricky. The original "play" of the card (e.g. '7') should have already put it on discard.
            // The game state's pending_action means we are now in the *input gathering phase* for that card's effect.
            // The player should not need to re-select the '7' card. They need to select a *different* card from their *current* hand.
             promptLabel.textContent = `Select a card from your hand to GIVE, then click "Confirm Swap Details".`;
             // We need a way for the player to select a card from hand and then click a new button here.
             // Let's assume they use the main hand display to select a card.
        }

        let targetPlayerName = null;
        if (pendingActionType === "SWAP_CARD_ANY") {
            const targetPlayerLabel = document.createElement('label');
            targetPlayerLabel.textContent = "Target Player for Swap:";
            pendingActionInputArea.appendChild(targetPlayerLabel);
            const targetPlayerSelect = document.createElement('select');
            gameState.players.forEach(p => {
                if (p.name !== मानव_खिलाड़ी_का_नाम) {
                    const option = document.createElement('option');
                    option.value = p.name;
                    option.textContent = p.name;
                    targetPlayerSelect.appendChild(option);
                }
            });
            pendingActionInputArea.appendChild(targetPlayerSelect);
            targetPlayerName = targetPlayerSelect.value; // initial
            targetPlayerSelect.onchange = () => targetPlayerName = targetPlayerSelect.value;
        }

        const cardToTakeLabel = document.createElement('label');
        cardToTakeLabel.textContent = "Index of card to TAKE from target player's hand (0-based):";
        pendingActionInputArea.appendChild(cardToTakeLabel);
        const cardToTakeInput = document.createElement('input');
        cardToTakeInput.type = 'number';
        cardToTakeInput.min = '0';
        pendingActionInputArea.appendChild(cardToTakeInput);

        const confirmButton = document.createElement('button');
        confirmButton.textContent = "Confirm Swap Details";
        confirmButton.onclick = async () => {
            const cardToGiveFromHandIdx = selected_card_index; // This should be a *new* selection from hand
            if (cardToGiveFromHandIdx === null) {
                logMessage("Error: You must select a card from your hand to give for the swap.", "error");
                return;
            }
            const actionPayload = {
                card_to_give_idx: cardToGiveFromHandIdx,
                card_to_take_idx: parseInt(cardToTakeInput.value)
            };
            if (pendingActionType === "SWAP_CARD_ANY") {
                // Find index of targetPlayerName
                const targetPIdx = gameState.players.findIndex(p => p.name === targetPlayerName);
                if (targetPIdx === -1) { logMessage("Error: Selected target player not found.", "error"); return;}
                actionPayload.target_player_idx = targetPIdx;
            }
            try {
                const result = await provideActionInputAPI(मानव_खिलाड़ी_का_नाम, actionPayload);
                logMessage(result.message);
                वर्तमान_खेल_की_स्थिति = result.game_state;
                renderAll();
            } catch (error) { /* already logged */ }
        };
        pendingActionInputArea.appendChild(confirmButton);


    } else if (pendingActionType === "DISCARD_FROM_PLAYER_HAND") {
        promptLabel.textContent = `Choose cards from ${actionData.victim_name}'s hand to discard. (UI for this is complex and pending full implementation).`;
        // Requires displaying victim's hand (or card count) and allowing selection of N cards.
        // Simplified: Ask for indices via prompt for now
        const indicesInputLabel = document.createElement('label');
        indicesInputLabel.textContent = `Indices of cards to discard from ${actionData.victim_name}'s hand (comma-separated, e.g., 0,2):`;
        pendingActionInputArea.appendChild(indicesInputLabel);
        const indicesInput = document.createElement('input');
        indicesInput.type = 'text';
        pendingActionInputArea.appendChild(indicesInput);

        const confirmButton = document.createElement('button');
        confirmButton.textContent = "Confirm Discard Selection";
        confirmButton.onclick = async () => {
            const indicesStr = indicesInput.value.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
            try {
                const result = await provideActionInputAPI(मानव_खिलाड़ी_का_नाम, { chosen_indices_from_victim: indicesStr });
                logMessage(result.message);
                वर्तमान_खेल_की_स्थिति = result.game_state;
                renderAll();
            } catch (error) { /* already logged */ }
        };
        pendingActionInputArea.appendChild(confirmButton);
    }
    // Add more pending actions here: PLAY_ANY_AND_DRAW_ONE is handled by play_card if card_index is passed.
    else {
        promptLabel.textContent = `Unhandled pending action: ${pendingActionType}. Please check game logic.`;
    }
}


function renderAll() {
    if (!वर्तमान_खेल_की_स्थिति) return;

    const humanPlayer = वर्तमान_खेल_की_स्थिति.players.find(p => p.name === मानव_खिलाड़ी_का_नाम);

    renderOpponents(वर्तमान_खेल_की_स्थिति.players);
    renderGameStatus(वर्तमान_खेल_की_स्थिति);
    if (humanPlayer) {
        renderPlayerHand(humanPlayer.hand); // Assumes player object has 'hand' array of card objects
    } else {
        renderPlayerHand([]); // Human player not found or no hand data
        logMessage(`Error: Human player ${मानव_खिलाड़ी_का_नाम} not found in game state.`, 'error');
    }

    renderPendingActionUI(वर्तमान_खेल_की_स्थिति.pending_action, वर्तमान_खेल_की_स्थिति.action_data, वर्तमान_खेल_की_स्थिति);

    // Show/hide CPU turn button
    if (वर्तमान_खेल_की_स्थिति.current_player_name !== मानव_खिलाड़ी_का_नाम && !वर्तमान_खेल_की_स्थिति.pending_action && !वर्तमान_खेल_की_स्थिति.game_over) {
        cpuTurnArea.style.display = 'block';
        standardActionsArea.style.display = 'none'; // Hide player actions
        pendingActionInputArea.innerHTML = ''; // Clear pending actions
    } else {
        cpuTurnArea.style.display = 'none';
    }

    if (वर्तमान_खेल_की_स्थिति.game_over) {
        logMessage(`Game Over! Winner: ${वर्तमान_खेल_की_स्थिति.winner || 'None'}`, 'success');
        playCardButton.disabled = true;
        drawCardButton.disabled = true;
        cpuTurnButton.disabled = true;
        pendingActionInputArea.innerHTML = `<p><strong>Game Over! Winner: ${वर्तमान_खेल_की_स्थिति.winner || 'None'}</strong></p>`;
    }
}

// --- Event Handlers ---
async function handlePlayCard() {
    if (चयनित_कार्ड_का_सूचकांक === null) {
        logMessage("No card selected to play.", "error");
        return;
    }

    const player = वर्तमान_खेल_की_स्थिति.players.find(p => p.name === मानव_खिलाड़ी_का_नाम);
    if (!player || !player.hand) {
        logMessage("Error: Could not find player's hand.", "error");
        return;
    }
    const cardToPlay = player.hand[चयनित_कार्ड_का_सूचकांक];

    let chosenColorForWild = null;
    if (cardToPlay.rank === "WILD" || cardToPlay.rank === "WILD_DRAW_FOUR") {
        // The backend API /play_card now handles prompting for color if not provided.
        // So, we can call it directly. If it needs a color, it will return next_action_prompt: "CHOOSE_COLOR".
        // The renderPendingActionUI will then handle showing color choices.
        // No need for a window.prompt here anymore if API and renderPendingActionUI handle it.
    }

    try {
        playCardButton.disabled = true; // Disable while processing
        const result = await playCardAPI(मानవ_खिलाड़ी_का_नाम, चयनित_कार्ड_का_सूचकांक, chosenColorForWild);
        logMessage(result.message);
        वर्तमान_खेल_की_स्थिति = result.game_state;
        चयनित_कार्ड_का_सूचकांक = null; // Reset selected card
        renderAll();
    } catch (error) {
        // Error already logged by fetchFromAPI. Button will re-enable via renderAll if appropriate.
        // If the error json contains game_state, it would have been updated by fetchFromAPI.
        // So, just ensure renderAll() is called to reflect any state received with the error.
        renderAll();
    }
}

async function handleDrawCard() {
    try {
        drawCardButton.disabled = true;
        const result = await drawCardAPI(मानव_खिलाड़ी_का_नाम);
        logMessage(result.message);
        वर्तमान_खेल_की_स्थिति = result.game_state;
        renderAll();
    } catch (error) {
        // Error already logged. Button will re-enable via renderAll if appropriate.
        renderAll();
    }
}

async function handleCpuTurn() {
    if (वर्तमान_खेल_की_स्थिति && वर्तमान_खेल_की_स्थिति.current_player_name !== मानव_खिलाड़ी_का_नाम) {
        try {
            cpuTurnButton.disabled = true;
            // This is a placeholder. The actual implementation depends on how CPU turns are managed.
            // For now, we assume this call would make the CPU play and return the new state.
            // A dedicated backend endpoint /api/cpu_play_turn would be needed.
            logMessage(`Simulating turn for ${वर्तमान_खेल_की_स्थिति.current_player_name}...`);

            // const result = await cpuPlayTurnAPI(वर्तमान_खेल_की_स्थिति.current_player_name);
            // For now, just re-fetch state, assuming backend might have advanced if it were a real game.
            // This is a stop-gap until a proper CPU turn API endpoint exists.
            // If the backend doesn't auto-play CPUs, this button won't do much other than show a message and refresh.
            // The proper solution is an endpoint that tells the backend: "Hey, it's CPU X's turn, make them play."

            // Let's modify this to call a generic "advance turn if CPU" endpoint or just refresh.
            // For a true simulation button, we need a backend endpoint.
            // Fallback: just fetch game state, assuming backend game loop might advance CPU.
            // This is NOT ideal.
            alert("CPU turn simulation needs a dedicated backend endpoint that makes the CPU play. For now, this button will just refresh the game state. If the backend has logic for CPU auto-play, it might reflect. Otherwise, manual calls for CPU via API tester would be needed.");
            const updatedState = await getGameState();
            वर्तमान_खेल_की_स्थिति = updatedState; // game_state is directly the object
            logMessage( "Attempted to refresh state after CPU turn simulation.");

            renderAll();
        } catch (error) {
            logMessage(`Error during CPU turn simulation: ${error.message}`, 'error');
            renderAll(); // Re-enable button if error
        }
    } else {
        logMessage("It's not a CPU's turn.", "info");
    }
}


// --- Initial Game Load ---
async function initGame() {
    try {
        const initialState = await getGameState();
        वर्तमान_खेल_की_स्थिति = initialState; // game_state is directly the object
        मानव_खिलाड़ी_का_नाम = initialState.players.find(p => !p.name.toLowerCase().includes("cpu"))?.name || "Player 1"; // Simple way to find a human
        logMessage("Game loaded successfully. Welcome!");
        renderAll();
    } catch (error) {
        logMessage("Failed to initialize game. Please check the server.", "error");
        // console.error("Initialization failed:", error);
    }
}
