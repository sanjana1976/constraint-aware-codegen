import * as vscode from 'vscode';
import { HILDEAPI } from '../utils/hildeAPI';

export class HILDEAnalysisProvider implements vscode.HoverProvider {
    private api: HILDEAPI;

    constructor() {
        this.api = new HILDEAPI();
    }

    async provideHover(
        document: vscode.Document,
        position: vscode.Position,
        token: vscode.CancellationToken
    ): Promise<vscode.Hover | null> {
        try {
            // Check if position is in a highlighted token
            const response = await this.api.getCompletionWithAnalysis(document.getText());
            
            if (!response) {
                return null;
            }

            const charPosition = this.getCharacterPosition(document, position);
            const highlightedIndex = response.highlighted_positions.indexOf(charPosition);
            
            if (highlightedIndex === -1) {
                return null;
            }

            // Get alternatives for this position
            const alternatives = response.top_k_tokens[charPosition];
            if (!alternatives || alternatives.length < 2) {
                return null;
            }

            // Create hover content
            const content = this.createHoverContent(alternatives, response.corrected_entropy_scores[charPosition]);
            
            return new vscode.Hover(content);
            
        } catch (error) {
            console.error('HILDE hover analysis failed:', error);
            return null;
        }
    }

    private getCharacterPosition(document: vscode.Document, position: vscode.Position): number {
        let charPos = 0;
        for (let line = 0; line < position.line; line++) {
            charPos += document.lineAt(line).text.length + 1; // +1 for newline
        }
        charPos += position.character;
        return charPos;
    }

    private createHoverContent(alternatives: any[], entropy: number): vscode.MarkdownString {
        const markdown = new vscode.MarkdownString();
        
        markdown.appendMarkdown(`## HILDE Analysis\n\n`);
        markdown.appendMarkdown(`**Entropy Score:** ${entropy.toFixed(3)}\n\n`);
        
        markdown.appendMarkdown(`### Alternatives:\n\n`);
        
        alternatives.forEach((alt, index) => {
            const isTop = index === 0;
            const marker = isTop ? '🟢' : '🔵';
            const analysis = alt.analysis;
            
            markdown.appendMarkdown(`${marker} **${alt.token}** (${(alt.probability * 100).toFixed(1)}%)\n`);
            
            if (analysis) {
                markdown.appendMarkdown(`- **Category:** ${analysis.category}\n`);
                markdown.appendMarkdown(`- **Importance:** ${(analysis.importance_score * 100).toFixed(0)}%\n`);
                markdown.appendMarkdown(`- **Summary:** ${analysis.explanation_summary}\n\n`);
            } else {
                markdown.appendMarkdown(`- No analysis available\n\n`);
            }
        });

        markdown.appendMarkdown(`---\n`);
        markdown.appendMarkdown(`*Click to see alternatives or use HILDE commands*`);
        
        return markdown;
    }
}
