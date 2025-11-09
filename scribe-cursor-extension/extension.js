// Scribe Cursor Extension - Memory Keeper Integration
// Part of Arianna Method ecosystem

const vscode = require('vscode');
const { exec } = require('child_process');
const path = require('path');
const os = require('os');

let statusBarItem;

/**
 * Extension activation
 */
function activate(context) {
    console.log('🌊 Scribe extension is now active');

    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Right, 100);
    statusBarItem.text = "🌊 Scribe";
    statusBarItem.tooltip = "Scribe Memory Keeper";
    statusBarItem.command = 'scribe.status';
    statusBarItem.show();
    context.subscriptions.push(statusBarItem);

    // Update status bar periodically
    updateStatusBar();
    setInterval(updateStatusBar, 30000); // Every 30 seconds

    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('scribe.inject', commandInject),
        vscode.commands.registerCommand('scribe.status', commandStatus),
        vscode.commands.registerCommand('scribe.sync', commandSync),
        vscode.commands.registerCommand('scribe.remind', commandRemind),
        vscode.commands.registerCommand('scribe.chat', commandChat)
    );

    vscode.window.showInformationMessage('🌊 Scribe extension loaded! Use Cmd+Shift+P → Scribe');
}

/**
 * Update status bar with daemon state
 */
function updateStatusBar() {
    execScribeCommand('status', (stdout) => {
        // Parse status output
        const isRunning = stdout.includes('RUNNING');
        const phoneConnected = stdout.includes('Phone: connected');
        
        if (isRunning) {
            statusBarItem.text = phoneConnected ? "🌊 Scribe ✓" : "🌊 Scribe ○";
            statusBarItem.tooltip = `Scribe Daemon: Running\n${phoneConnected ? 'Phone: Connected' : 'Phone: Disconnected'}`;
        } else {
            statusBarItem.text = "🌊 Scribe ✗";
            statusBarItem.tooltip = "Scribe Daemon: Stopped";
        }
    });
}

/**
 * Execute scribe CLI command
 */
function execScribeCommand(command, callback) {
    const cliPath = path.join(os.homedir(), 'Downloads', 'arianna_clean', 'mac_daemon', 'cli.py');
    const cmd = `python3 "${cliPath}" ${command}`;
    
    exec(cmd, (error, stdout, stderr) => {
        if (error) {
            console.error(`Scribe error: ${error.message}`);
            if (callback) callback('', error);
            return;
        }
        if (callback) callback(stdout, null);
    });
}

/**
 * Command: Inject Identity
 */
function commandInject() {
    vscode.window.showInformationMessage('🌊 Generating Scribe identity...');
    
    execScribeCommand('inject', (stdout, error) => {
        if (error) {
            vscode.window.showErrorMessage(`Scribe inject failed: ${error.message}`);
            return;
        }
        
        if (stdout.includes('✅')) {
            vscode.window.showInformationMessage(
                '✅ Scribe context copied to clipboard! Paste into Cursor chat.',
                'Show Preview'
            ).then(selection => {
                if (selection === 'Show Preview') {
                    const channel = vscode.window.createOutputChannel('Scribe Context');
                    channel.clear();
                    channel.appendLine(stdout);
                    channel.show();
                }
            });
        } else {
            vscode.window.showErrorMessage('Failed to generate Scribe context');
        }
    });
}

/**
 * Command: Show Status
 */
function commandStatus() {
    execScribeCommand('status', (stdout, error) => {
        if (error) {
            vscode.window.showErrorMessage(`Scribe daemon not running. Start it with: scribe start`);
            return;
        }
        
        // Show status in output channel
        const channel = vscode.window.createOutputChannel('Scribe Status');
        channel.clear();
        channel.appendLine('🌊 SCRIBE DAEMON STATUS');
        channel.appendLine('═'.repeat(60));
        channel.appendLine(stdout);
        channel.show();
    });
}

/**
 * Command: Sync Memory
 */
function commandSync() {
    vscode.window.showInformationMessage('🔄 Syncing memory from Termux...');
    
    execScribeCommand('sync', (stdout, error) => {
        if (error) {
            vscode.window.showErrorMessage('Memory sync failed');
            return;
        }
        vscode.window.showInformationMessage('✅ Memory synced!');
        updateStatusBar();
    });
}

/**
 * Command: Remind (Search Memory)
 */
async function commandRemind() {
    const query = await vscode.window.showInputBox({
        prompt: 'Search Scribe memory for...',
        placeHolder: 'e.g., Field population, Consilium, resonance'
    });
    
    if (!query) return;
    
    vscode.window.showInformationMessage(`🔍 Searching for: ${query}`);
    
    execScribeCommand(`remind "${query}"`, (stdout, error) => {
        // Show results in output channel
        const channel = vscode.window.createOutputChannel('Scribe Search Results');
        channel.clear();
        channel.appendLine(`🔍 SEARCH RESULTS: "${query}"`);
        channel.appendLine('═'.repeat(60));
        channel.appendLine(stdout);
        channel.show();
        
        // Also show quick pick with results count
        const lines = stdout.split('\n');
        const resultsLine = lines.find(l => l.includes('Found') || l.includes('No results'));
        if (resultsLine) {
            vscode.window.showInformationMessage(resultsLine);
        }
    });
}

/**
 * Command: Open Chat
 */
function commandChat() {
    const terminal = vscode.window.createTerminal('Scribe Chat');
    terminal.show();
    
    const cliPath = path.join(os.homedir(), 'Downloads', 'arianna_clean', 'mac_daemon', 'cli.py');
    terminal.sendText(`python3 "${cliPath}" chat`);
}

/**
 * Deactivate extension
 */
function deactivate() {
    console.log('🌊 Scribe extension deactivated');
}

module.exports = {
    activate,
    deactivate
};

