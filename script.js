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

async function cpuPlayTurnAPI(playerName) {
    logMessage(`Requesting CPU ${playerName} to play...`);
    return fetchFromAPI("/cpu_play_turn", 'POST', { player_name: playerName });
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
        // Add color specific classes for styling
        if (card.color) { // card.color is "RED", "BLUE", "WILD" etc.
            cardDiv.classList.add(`color-${card.color}`);
        }
        // Ranks like WILD, WILD_DRAW_FOUR already have color WILD.
        // Specific rank classes can be added if defined in CSS, e.g. rank-SKIP, rank-DRAW_TWO
        cardDiv.classList.add(`rank-${card.rank}`);


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
    let actorForPendingActionName = null;
    let humanIsActor = false;

    if (actionData && gameState.players) { // Ensure actionData and players are available
        let actorIdx = -1;
        if (pendingActionType === "CHOOSE_COLOR") {
            actorIdx = actionData.is_for_rank_6_wild ? actionData.original_player_idx : actionData.player_idx;
        } else if (["SWAP_CARD_RIGHT", "SWAP_CARD_ANY", "PLAY_ANY_AND_DRAW_ONE"].includes(pendingActionType)) {
            actorIdx = actionData.original_player_idx;
        } else if (pendingActionType === "DISCARD_FROM_PLAYER_HAND") {
            actorIdx = actionData.chooser_idx;
        }

        if (actorIdx !== undefined && actorIdx !== -1 && gameState.players[actorIdx]) {
            actorForPendingActionName = gameState.players[actorIdx].name;
            if (gameState.players[actorIdx].player_type === "HUMAN" && actorForPendingActionName === मानव_खिलाड़ी_का_नाम) {
                humanIsActor = true;
            }
        }
    }

    if (!humanIsActor) {
        const waitingFor = actorForPendingActionName || gameState.current_player_name; // Fallback to current player if specific actor not found
        logMessage(`Waiting for ${waitingFor} to resolve ${pendingActionType}...`);
        pendingActionInputArea.innerHTML = `<p>Waiting for ${waitingFor} to act on: ${pendingActionType}</p>`;
        // Disable all human action buttons
        playCardButton.disabled = true;
        drawCardButton.disabled = true;
        return;
    }
    // If human is the actor, pendingActionInputArea will be populated below.
    // Standard action buttons (play/draw) are already hidden by renderAll logic if pending_action exists.

    const promptContainer = document.createElement('div');
    promptContainer.className = 'pending-action-prompt';

    const promptLabel = document.createElement('h3'); // Changed to h3 for better semantics
    promptContainer.appendChild(promptLabel);
    pendingActionInputArea.appendChild(promptContainer);

    if (pendingActionType === "CHOOSE_COLOR") {
        promptLabel.textContent = "Choose a color for the Wild card:";
        const colors = ["RED", "YELLOW", "GREEN", "BLUE"];
        colors.forEach(color => {
            const button = document.createElement('button');
            button.textContent = color;
            // Using existing CSS classes like .color-RED from style.css for buttons too
            button.className = `color-choice-button color-${color.toUpperCase()}`;
            // Basic inline styles for immediate visual feedback if CSS isn't fully covering buttons
            button.style.backgroundColor = color.toLowerCase();
            if (color === "YELLOW") button.style.color = "black"; else button.style.color = "white";

            button.addEventListener('click', async () => {
                try {
                    const result = await provideActionInputAPI(मानव_खिलाड़ी_का_नाम, { chosen_color: color });
                    logMessage(result.message);
                    वर्तमान_खेल_की_स्थिति = result.game_state;
                    renderAll();
                    triggerCpuTurnIfApplicable();
                } catch (error) {
                    // Error already logged by fetchFromAPI
                }
            });
            });
            promptContainer.appendChild(button);
        });
    } else if (pendingActionType === "PLAY_ANY_AND_DRAW_ONE") {
        promptLabel.textContent = "Rank 6 effect: Play any card from your hand, then you will draw one.";
        // Re-enable standard play/draw area for this specific pending action.
        // The player will select a card and click the main "Play Selected Card" button.
        standardActionsArea.style.display = 'flex';
        playCardButton.disabled = (चयनित_कार्ड_का_सूचकांक === null) || isCpuTurnInProgress; // Keep CPU check
        drawCardButton.disabled = true; // Cannot just draw during this specific action
        logMessage("Select any card from your hand and click 'Play Selected Card'.");

    } else if (pendingActionType === "SWAP_CARD_RIGHT" || pendingActionType === "SWAP_CARD_ANY") {
        promptLabel.textContent = `Action: ${pendingActionType}`;

        const explanation = document.createElement('p');
        promptContainer.appendChild(explanation);

        if (pendingActionType === "SWAP_CARD_ANY") {
            // SWAP_CARD_ANY has two phases for human: 1. Choose target player, 2. Choose cards.
            // actionData from backend should indicate which phase.
            // If actionData.target_player_idx is NOT set, it's phase 1.
            if (actionData.target_player_idx === undefined || actionData.target_player_idx === null) {
                explanation.textContent = "First, choose the target player for the swap.";
                const targetPlayerLabel = document.createElement('label');
                targetPlayerLabel.textContent = "Target Player for Swap:";
                promptContainer.appendChild(targetPlayerLabel);

                const targetPlayerSelect = document.createElement('select');
                targetPlayerSelect.id = "swap-target-player-select";
                gameState.players.forEach((p, idx) => {
                    if (p.player_type !== "HUMAN" || p.name !== मानव_खिलाड़ी_का_नाम) { // Can target CPUs or other humans
                        if (p.name !== मानव_खिलाड़ी_का_नाम) { // Cannot target self
                           const option = document.createElement('option');
                           option.value = idx.toString(); // Store index
                           option.textContent = `${p.name} (${p.card_count} cards)`;
                           targetPlayerSelect.appendChild(option);
                        }
                    }
                });
                promptContainer.appendChild(targetPlayerSelect);

                const confirmTargetButton = document.createElement('button');
                confirmTargetButton.textContent = "Confirm Target Player";
                confirmTargetButton.onclick = async () => {
                    const targetIdx = parseInt(document.getElementById('swap-target-player-select').value);
                    try {
                        const result = await provideActionInputAPI(मानవ_खिलाड़ी_का_नाम, { target_player_idx: targetIdx });
                        logMessage(result.message);
                        वर्तमान_खेल_की_स्थिति = result.game_state;
                        renderAll();
                        // Still human's turn for multi-step action, so no triggerCpuTurnIfApplicable yet.
                    } catch (error) { /* already logged */ }
                };
                promptContainer.appendChild(confirmTargetButton);
                return; // End here for phase 1 of SWAP_CARD_ANY
            } else {
                // Phase 2: Target player is known (from actionData.target_player_idx), now choose cards.
                const targetPlayer = gameState.players[actionData.target_player_idx];
                explanation.textContent = `You are swapping with ${targetPlayer.name}. Select a card from YOUR hand to give. Then, specify the index (0-based) of the card to take from ${targetPlayer.name}'s hand (they have ${targetPlayer.card_count} cards).`;
            }
        } else { // SWAP_CARD_RIGHT
             const humanPlayerIndex = gameState.players.findIndex(p => p.name === मानव_खिलाड़ी_का_नाम);
             const playerToRightIdx = (humanPlayerIndex + gameState.play_direction + gameState.players.length) % gameState.players.length;
             const playerToRight = gameState.players[playerToRightIdx];
             explanation.textContent = `You are swapping with ${playerToRight.name} (player to your ${gameState.play_direction === 1 ? 'right' : 'left'}). Select a card from YOUR hand to give. Then, specify the index (0-based) of the card to take from ${playerToRight.name}'s hand (they have ${playerToRight.card_count} cards).`;
        }

        const cardToGivePrompt = document.createElement('p');
        cardToGivePrompt.innerHTML = "<strong>1. Select a card from your hand above to give.</strong>";
        promptContainer.appendChild(cardToGivePrompt);

        const cardToTakeLabel = document.createElement('label');
        cardToTakeLabel.htmlFor = 'swap-card-to-take-idx';
        cardToTakeLabel.innerHTML = "<strong>2. Index of card to TAKE from target's hand (0-based):</strong>";
        promptContainer.appendChild(cardToTakeLabel);
        const cardToTakeInput = document.createElement('input');
        cardToTakeInput.type = 'number';
        cardToTakeInput.min = '0';
        cardToTakeInput.id = 'swap-card-to-take-idx';
        promptContainer.appendChild(cardToTakeInput);

        const confirmButton = document.createElement('button');
        confirmButton.textContent = "Confirm Swap";
        confirmButton.onclick = async () => {
            const cardToGiveFromHandIdx = चयनित_कार्ड_का_सूचकांक;
            if (cardToGiveFromHandIdx === null) {
                logMessage("Error: You must select a card from YOUR hand to give.", "error");
                return;
            }
            const cardToTakeIdxValue = parseInt(document.getElementById('swap-card-to-take-idx').value);
            if (isNaN(cardToTakeIdxValue) || cardToTakeIdxValue < 0) {
                 logMessage("Error: Invalid index for card to take.", "error");
                return;
            }

            const actionPayload = {
                card_to_give_idx: cardToGiveFromHandIdx,
                card_to_take_idx: cardToTakeIdxValue
            };

            if (pendingActionType === "SWAP_CARD_ANY") {
                if (actionData.target_player_idx === undefined) {
                     logMessage("Error: Target player for SWAP_CARD_ANY not determined.", "error"); return;
                }
                actionPayload.target_player_idx = actionData.target_player_idx;
            }

            try {
                const result = await provideActionInputAPI(मानవ_खिलाड़ी_का_नाम, actionPayload);
                logMessage(result.message);
                वर्तमान_खेल_की_स्थिति = result.game_state;
                renderAll();
                triggerCpuTurnIfApplicable();
            } catch (error) { /* already logged */ }
        };
        promptContainer.appendChild(confirmButton);

    } else if (pendingActionType === "DISCARD_FROM_PLAYER_HAND") {
        const victimPlayer = gameState.players[actionData.victim_idx]; // Player who played blue 3
        const chooserPlayer = gameState.players[actionData.chooser_idx]; // Player who must choose (human)
        const numToDiscard = actionData.count || 2;

        promptLabel.textContent = `Action: ${victimPlayer.name} played Blue 3!`;
        const explanation = document.createElement('p');
        explanation.textContent = `You (${chooserPlayer.name}) must choose ${numToDiscard} card(s) from ${victimPlayer.name}'s hand for them to discard. ${victimPlayer.name} has ${victimPlayer.card_count} cards.`;
        promptContainer.appendChild(explanation);

        const indicesInputLabel = document.createElement('label');
        indicesInputLabel.htmlFor = 'discard-indices-input';
        indicesInputLabel.textContent = `Enter ${numToDiscard} card index/indices (0-based, comma-separated if multiple) from ${victimPlayer.name}'s hand:`;
        promptContainer.appendChild(indicesInputLabel);

        const indicesInput = document.createElement('input');
        indicesInput.type = 'text';
        indicesInput.id = 'discard-indices-input';
        indicesInput.placeholder = numToDiscard === 1 ? "e.g., 0" : "e.g., 0,2";
        promptContainer.appendChild(indicesInput);

        const confirmButton = document.createElement('button');
        confirmButton.textContent = "Confirm Discard Selection";
        confirmButton.onclick = async () => {
            const indicesStr = document.getElementById('discard-indices-input').value;
            const chosenIndices = indicesStr.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));

            // Validate chosen indices count
            const uniqueIndices = [...new Set(chosenIndices)];
            if (uniqueIndices.length !== numToDiscard) {
                logMessage(`Error: You must select exactly ${numToDiscard} unique card indices.`, 'error');
                return;
            }
            // Further validation (are indices in range of victim's hand) should be done by backend
            // but a simple client-side check can be useful too.
            for(const idx of uniqueIndices){
                if(idx < 0 || idx >= victimPlayer.card_count){
                    logMessage(`Error: Index ${idx} is out of range for ${victimPlayer.name}'s hand (0-${victimPlayer.card_count-1}).`, 'error');
                    return;
                }
            }

            try {
                const result = await provideActionInputAPI(मानవ_खिलाड़ी_का_नाम, { chosen_indices_from_victim: uniqueIndices });
                logMessage(result.message);
                वर्तमान_खेल_की_स्थिति = result.game_state;
                renderAll();
                triggerCpuTurnIfApplicable();
            } catch (error) { /* already logged */ }
        };
        promptContainer.appendChild(confirmButton);
    } else {
        promptLabel.textContent = `Unhandled pending action for human: ${pendingActionType}.`;
        logMessage(`Info: Waiting for action on ${pendingActionType}. If this is unexpected, check console or backend.`, "info");
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

    const currentPlayer = वर्तमान_खेल_की_स्थिति.players.find(p => p.name === वर्तमान_खेल_की_स्थिति.current_player_name);
    const isHumanTurn = currentPlayer && currentPlayer.player_type === "HUMAN" && currentPlayer.name === मानव_खिलाड़ी_का_नाम;

    if (वर्तमान_खेल_की_स्थिति.game_over) {
        logMessage(`Game Over! Winner: ${वर्तमान_खेल_की_स्थिति.winner || 'None'}`, 'success');
        playCardButton.disabled = true;
        drawCardButton.disabled = true;
        cpuTurnButton.disabled = true; // Manual CPU button
        standardActionsArea.style.display = 'none';
        pendingActionInputArea.innerHTML = `<p><strong>Game Over! Winner: ${वर्तमान_खेल_की_स्थिति.winner || 'None'}</strong></p>`;
        cpuTurnArea.style.display = 'none';
    } else if (वर्तमान_खेल_की_स्थिति.pending_action) {
        // If there's a pending action, renderPendingActionUI handles UI for the actor.
        // Standard actions should be hidden.
        standardActionsArea.style.display = 'none';
        cpuTurnArea.style.display = 'none';
        // playCardButton and drawCardButton are handled by renderPendingActionUI if human is actor,
        // or disabled if human is not actor by the logic within renderPendingActionUI.
    } else if (isHumanTurn) {
        standardActionsArea.style.display = 'flex';
        playCardButton.disabled = (चयनित_कार्ड_का_सूचकांक === null) || isCpuTurnInProgress;
        drawCardButton.disabled = isCpuTurnInProgress;
        cpuTurnArea.style.display = 'none';
        pendingActionInputArea.innerHTML = ''; // Clear any old pending action UI
    } else { // CPU's turn (and no pending action for human)
        standardActionsArea.style.display = 'none';
        pendingActionInputArea.innerHTML = ''; // Clear any old pending action UI
        playCardButton.disabled = true;
        drawCardButton.disabled = true;
        // cpuTurnArea.style.display = 'block'; // If manual CPU button is desired
        // For auto CPU turns, this button might not be shown or needed.
        // If it's a CPU turn, triggerCpuTurnIfApplicable should have been called.
        cpuTurnButton.disabled = isCpuTurnInProgress; // Reflects if manual button is active
        if (isCpuTurnInProgress) {
             logMessage(`CPU ${currentPlayer.name} is processing...`);
        }
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
        triggerCpuTurnIfApplicable(); // Check if CPU should play next
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
        const result = await drawCardAPI(मानవ_खिलाड़ी_का_नाम);
        logMessage(result.message);
        वर्तमान_खेल_की_स्थिति = result.game_state;
        renderAll();
        triggerCpuTurnIfApplicable(); // Check if CPU should play next
    } catch (error) {
        // Error already logged. Button will re-enable via renderAll if appropriate.
        renderAll();
    }
}

let isCpuTurnInProgress = false; // Flag to prevent overlapping CPU turn calls

async function handleCpuTurn() {
    if (!वर्तमान_खेल_की_स्थिति || वर्तमान_खेल_की_स्थिति.game_over || isCpuTurnInProgress) {
        return;
    }

    const currentPlayerName = वर्तमान_खेल_की_स्थिति.current_player_name;
    const currentPlayer = वर्तमान_खेल_की_स्थिति.players.find(p => p.name === currentPlayerName);

    if (!currentPlayer || currentPlayer.player_type !== "CPU") {
        // logMessage("Not a CPU's turn or player not found.", "debug");
        return;
    }

    isCpuTurnInProgress = true;
    cpuTurnButton.disabled = true; // Keep this for manual trigger if needed, or disable generally
    logMessage(`CPU ${currentPlayerName} is thinking...`);

    try {
        // Add a small delay for UX
        await new Promise(resolve => setTimeout(resolve, 1000));

        const result = await cpuPlayTurnAPI(currentPlayerName);
        logMessage(result.message || `CPU ${currentPlayerName} completed its turn.`);
        वर्तमान_खेल_की_स्थिति = result.game_state;
        renderAll(); // Render before checking for next CPU turn

        if (वर्तमान_खेल_की_स्थिति && !वर्तमान_खेल_की_स्थिति.game_over) {
            // Check if the next player is also a CPU and trigger their turn
            const nextPlayerName = वर्तमान_खेल_की_स्थिति.current_player_name;
            const nextPlayer = वर्तमान_खेल_की_स्थिति.players.find(p => p.name === nextPlayerName);

            let humanActorRequiredForNextPendingAction = false;
            if (वर्तमान_खेल_की_स्थिति.pending_action && वर्तमान_खेल_की_स्थिति.action_data) {
                const paData = वर्तमान_खेल_की_स्थिति.action_data;
                const paType = वर्तमान_खेल_की_स्थिति.pending_action;
                let actorIdx;
                if (paType === "CHOOSE_COLOR") {
                    actorIdx = paData.is_for_rank_6_wild ? paData.original_player_idx : paData.player_idx;
                } else if (["SWAP_CARD_RIGHT", "SWAP_CARD_ANY", "PLAY_ANY_AND_DRAW_ONE"].includes(paType)) {
                    actorIdx = paData.original_player_idx;
                } else if (paType === "DISCARD_FROM_PLAYER_HAND") {
                    actorIdx = paData.chooser_idx;
                }
                if (actorIdx !== undefined && वर्तमान_खेल_की_स्थिति.players[actorIdx] && वर्तमान_खेल_की_स्थिति.players[actorIdx].player_type === "HUMAN") {
                    humanActorRequiredForNextPendingAction = true;
                }
            }

            if (nextPlayer && nextPlayer.player_type === "CPU" && !humanActorRequiredForNextPendingAction) {
                // If the next player is CPU AND there's no pending action OR the pending action is not for a human
                setTimeout(() => {
                    isCpuTurnInProgress = false;
                    handleCpuTurn();
                }, 100);
            } else {
                 isCpuTurnInProgress = false;
            }
        } else {
            isCpuTurnInProgress = false; // Game is over
        }
    } catch (error) {
        logMessage(`Error during CPU ${currentPlayerName}'s turn: ${error.message}`, 'error');
        // वर्तमान_खेल_की_स्थिति might have been updated by fetchFromAPI with error details
        renderAll();
        isCpuTurnInProgress = false;
    } finally {
        // Update button state based on whether next turn is human or CPU auto-plays
        const nextPlayer = वर्तमान_खेल_की_स्थिति ? वर्तमान_खेल_की_स्थिति.players.find(p => p.name === वर्तमान_खेल_की_स्थिति.current_player_name) : null;
        const nextIsCpu = nextPlayer && nextPlayer.player_type === "CPU";
        // Disable manual CPU button if a CPU turn is in progress, or if it's human's turn, or if game is over
        cpuTurnButton.disabled = isCpuTurnInProgress || !nextIsCpu || (वर्तमान_खेल_की_स्थिति && वर्तमान_खेल_की_स्थिति.game_over);
    }
}

function triggerCpuTurnIfApplicable() {
    if (!वर्तमान_खेल_की_स्थिति || वर्तमान_खेल_की_स्थिति.game_over || isCpuTurnInProgress) {
        return;
    }
    const currentPlayer = वर्तमान_खेल_की_स्थिति.players.find(p => p.name === वर्तमान_खेल_की_स्थिति.current_player_name);

    if (currentPlayer && currentPlayer.player_type === "CPU") {
        // Check if there's a pending action that requires HUMAN input.
        // If so, don't auto-trigger CPU.
        let humanActorRequiredForPending = false;
        if (वर्तमान_खेल_की_स्थिति.pending_action && वर्तमान_खेल_की_स्थिति.action_data) {
            const paData = वर्तमान_खेल_की_स्थिति.action_data;
            const paType = वर्तमान_खेल_की_स्थिति.pending_action; // This is a string e.g. "CHOOSE_COLOR"
            let actorIdx;

            if (paType === "CHOOSE_COLOR") {
                actorIdx = paData.is_for_rank_6_wild ? paData.original_player_idx : paData.player_idx;
            } else if (["SWAP_CARD_RIGHT", "SWAP_CARD_ANY", "PLAY_ANY_AND_DRAW_ONE"].includes(paType)) {
                actorIdx = paData.original_player_idx;
            } else if (paType === "DISCARD_FROM_PLAYER_HAND") {
                actorIdx = paData.chooser_idx;
            }

            if (actorIdx !== undefined && वर्तमान_खेल_की_स्थिति.players[actorIdx] && वर्तमान_खेल_की_स्थिति.players[actorIdx].player_type === "HUMAN") {
                humanActorRequiredForPending = true;
            }
        }

        if (!humanActorRequiredForPending) {
            // Delay slightly to allow UI updates from previous action to render
            setTimeout(handleCpuTurn, 100);
        } else {
            logMessage("CPU turn, but pending action requires human input.", "info");
        }
    }
}


// --- Initial Game Load ---
async function initGame() {
    try {
        const initialState = await getGameState();
        वर्तमान_खेल_की_स्थिति = initialState; // game_state is directly the object
        const humanPlayerFound = initialState.players.find(p => p.player_type === "HUMAN");
        if (humanPlayerFound) {
            मानव_खिलाड़ी_का_नाम = humanPlayerFound.name;
        } else {
            // Fallback if no player is marked as HUMAN (should not happen with backend setup)
            मानव_खिलाड़ी_का_नाम = initialState.players[0]?.name || "Player 1";
            logMessage("Warning: No player explicitly marked as HUMAN. Defaulting to first player.", "error");
        }
        logMessage(`Game loaded successfully. Welcome, ${मानव_खिलाड़ी_का_नाम}!`);
        renderAll();
        triggerCpuTurnIfApplicable(); // Check if CPU should play first
    } catch (error) {
        logMessage("Failed to initialize game. Please check the server.", "error");
        // console.error("Initialization failed:", error);
    }
}
