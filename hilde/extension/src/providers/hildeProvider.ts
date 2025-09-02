import * as vscode from 'vscode';
import { HILDEAPI } from '../utils/hildeAPI';

export class HILDEProvider {
    private api: HILDEAPI;
    private decorations: Map<string, vscode.TextEditorDecorationType> = new Map();

    constructor() {
        this.api = new HILDEAPI();
        this.initializeDecorations();
    }

    private initializeDecorations() {
        // Create decoration types for different entropy levels
        const highEntropy = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 0, 0, 0.3)',
            border: '2px solid rgba(255, 0, 0, 0.8)',
            borderStyle: 'solid'
        });

        const mediumEntropy = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 165, 0, 0.2)',
            border: '1px solid rgba(255, 165, 0, 0.6)',
            borderStyle: 'solid'
        });

        const lowEntropy = vscode.window.createTextEditorDecorationType({
            backgroundColor: 'rgba(255, 255, 0, 0.1)',
            border: '1px dashed rgba(255, 255, 0, 0.4)',
            borderStyle: 'dashed'
        });

        this.decorations.set('high', highEntropy);
        this.decorations.set('medium', mediumEntropy);
        this.decorations.set('low', lowEntropy);
    }

    public async analyzeDocument(editor: vscode.TextEditor): Promise<void> {
        try {
            const document = editor.document;
            const text = document.getText();
            
            // Get completion with analysis from HILDE API
            const response = await this.api.getCompletionWithAnalysis(text);
            
            if (response && response.highlighted_positions) {
                this.applyDecorations(editor, response);
            }
        } catch (error) {
            console.error('HILDE analysis failed:', error);
        }
    }

    private applyDecorations(editor: vscode.TextEditor, response: any): void {
        const ranges: vscode.Range[] = [];
        
        // Apply decorations based on highlighted positions
        response.highlighted_positions.forEach((position: number) => {
            const entropy = response.corrected_entropy_scores[position];
            const decorationType = this.getDecorationType(entropy);
            
            if (decorationType) {
                const range = this.getRangeForPosition(editor.document, position);
                if (range) {
                    ranges.push(range);
                }
            }
        });

        // Apply decorations
        if (ranges.length > 0) {
            const decorationType = this.decorations.get('medium')!;
            editor.setDecorations(decorationType, ranges);
        }
    }

    private getDecorationType(entropy: number): vscode.TextEditorDecorationType | null {
        if (entropy > 0.7) return this.decorations.get('high') || null;
        if (entropy > 0.4) return this.decorations.get('medium') || null;
        if (entropy > 0.1) return this.decorations.get('low') || null;
        return null;
    }

    private getRangeForPosition(document: vscode.TextDocument, position: number): vscode.Range | null {
        // Convert position index to line/character position
        const text = document.getText();
        let currentPos = 0;
        
        for (let line = 0; line < document.lineCount; line++) {
            const lineText = document.lineAt(line).text;
            if (currentPos + lineText.length >= position) {
                const char = position - currentPos;
                return new vscode.Range(line, char, line, char + 1);
            }
            currentPos += lineText.length + 1; // +1 for newline
        }
        
        return null;
    }

    public dispose(): void {
        this.decorations.forEach(decoration => decoration.dispose());
        this.decorations.clear();
    }
}
