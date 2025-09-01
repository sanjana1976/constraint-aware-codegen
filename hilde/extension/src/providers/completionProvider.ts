import * as vscode from 'vscode';
import { HILDEAPI } from '../utils/hildeAPI';

export class HILDECompletionProvider implements vscode.CompletionItemProvider {
    private api: HILDEAPI;

    constructor() {
        this.api = new HILDEAPI();
    }

    async provideCompletionItems(
        document: vscode.TextDocument,
        position: vscode.Position,
        token: vscode.CancellationToken,
        context: vscode.CompletionContext
    ): Promise<vscode.CompletionItem[]> {
        try {
            const linePrefix = document.lineAt(position).text.substr(0, position.character);
            const documentText = document.getText();
            
            // Get HILDE completion with alternatives
            const response = await this.api.getCompletionWithAnalysis(documentText);
            
            if (!response) {
                return [];
            }

            const completionItems: vscode.CompletionItem[] = [];
            
            // Add main completion
            const mainCompletion = new vscode.CompletionItem(
                response.completion,
                vscode.CompletionItemKind.Text
            );
            mainCompletion.detail = 'HILDE Completion';
            mainCompletion.documentation = 'AI-generated code completion';
            completionItems.push(mainCompletion);

            // Add alternative completions for highlighted positions
            response.highlighted_positions.forEach((pos: number) => {
                const alternatives = response.top_k_tokens[pos];
                if (alternatives && alternatives.length > 1) {
                    alternatives.slice(1).forEach((alt: any, index: number) => {
                        const altCompletion = new vscode.CompletionItem(
                            alt.token,
                            vscode.CompletionItemKind.Text
                        );
                        altCompletion.detail = `Alternative ${index + 1}`;
                        altCompletion.documentation = alt.analysis?.explanation_summary || 'Alternative token';
                        
                        // Add command to replace token
                        altCompletion.command = {
                            command: 'hilde.replaceToken',
                            title: 'Replace with alternative',
                            arguments: [pos, alt.token]
                        };
                        
                        completionItems.push(altCompletion);
                    });
                }
            });

            return completionItems;
            
        } catch (error) {
            console.error('HILDE completion failed:', error);
            return [];
        }
    }
}
