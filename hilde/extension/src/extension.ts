import * as vscode from 'vscode';
import { HILDEProvider } from './providers/hildeProvider';
import { HILDECompletionProvider } from './providers/completionProvider';
import { HILDEAnalysisProvider } from './providers/analysisProvider';

export function activate(context: vscode.ExtensionContext) {
    console.log('HILDE Assistant is now active!');

    // Initialize providers
    const hildeProvider = new HILDEProvider();
    const completionProvider = new HILDECompletionProvider();
    const analysisProvider = new HILDEAnalysisProvider();

    // Register completion provider
    const completionDisposable = vscode.languages.registerCompletionItemProvider(
        { scheme: 'file', language: 'python' },
        completionProvider,
        '.', ' ', '('
    );

    // Register hover provider for token analysis
    const hoverDisposable = vscode.languages.registerHoverProvider(
        { scheme: 'file', language: 'python' },
        analysisProvider
    );

    // Register commands
    const startCommand = vscode.commands.registerCommand('hilde.start', () => {
        vscode.window.showInformationMessage('HILDE Assistant started!');
    });

    const toggleModeCommand = vscode.commands.registerCommand('hilde.toggleMode', () => {
        const config = vscode.workspace.getConfiguration('hilde');
        const currentMode = config.get('mode');
        const newMode = currentMode === 'intentional' ? 'efficient' : 'intentional';
        config.update('mode', newMode, vscode.ConfigurationTarget.Global);
        vscode.window.showInformationMessage(`HILDE mode switched to: ${newMode}`);
    });

    // Add to subscriptions
    context.subscriptions.push(
        completionDisposable,
        hoverDisposable,
        startCommand,
        toggleModeCommand
    );
}

export function deactivate() {}
