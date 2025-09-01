import axios from 'axios';
import * as vscode from 'vscode';

export interface HILDECompletionResponse {
    completion: string;
    tokens: any[];
    top_k_tokens: any[][];
    corrected_entropy_scores: number[];
    highlighted_positions: number[];
}

export class HILDEAPI {
    private baseUrl: string;
    private config: vscode.WorkspaceConfiguration;

    constructor() {
        this.config = vscode.workspace.getConfiguration('hilde');
        this.baseUrl = this.config.get('apiUrl', 'http://localhost:8000');
    }

    async getCompletionWithAnalysis(prompt: string): Promise<HILDECompletionResponse | null> {
        try {
            const response = await axios.post(`${this.baseUrl}/hilde/completion`, {
                prompt: prompt,
                max_tokens: 100,
                temperature: 0.1,
                top_k: 10,
                enable_analysis: true
            }, {
                timeout: 30000,
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            return response.data;
        } catch (error) {
            console.error('HILDE API request failed:', error);
            return null;
        }
    }

    async replaceToken(position: number, newToken: string, context: string): Promise<boolean> {
        try {
            // This would trigger suffix regeneration in the backend
            const response = await axios.post(`${this.baseUrl}/hilde/regenerate`, {
                position: position,
                new_token: newToken,
                context: context
            });

            return response.status === 200;
        } catch (error) {
            console.error('Token replacement failed:', error);
            return false;
        }
    }

    async getSecurityAnalysis(code: string): Promise<any> {
        try {
            const response = await axios.post(`${this.baseUrl}/hilde/security`, {
                code: code
            });

            return response.data;
        } catch (error) {
            console.error('Security analysis failed:', error);
            return null;
        }
    }
}
