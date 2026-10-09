// Bedrock Converse API client utilities

export class BedrockConfigError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'BedrockConfigError';
  }
}

export interface BedrockConfig {
  token: string;
  region: string;
  modelId: string;
}

export function validateBedrockConfig(): BedrockConfig {
  const token = process.env.AWS_BEARER_TOKEN_BEDROCK;
  const region = process.env.AWS_REGION;
  const modelId = process.env.BEDROCK_MODEL_ID;

  console.log('[Bedrock Config Check]');
  console.log('- AWS_BEARER_TOKEN_BEDROCK:', token ? '✓ SET' : '✗ MISSING');
  console.log('- AWS_REGION:', region || '✗ MISSING');
  console.log('- BEDROCK_MODEL_ID:', modelId || '✗ MISSING');

  if (!token) {
    throw new BedrockConfigError('AWS_BEARER_TOKEN_BEDROCK environment variable is not set');
  }
  if (!region) {
    throw new BedrockConfigError('AWS_REGION environment variable is not set');
  }
  if (!modelId) {
    throw new BedrockConfigError('BEDROCK_MODEL_ID environment variable is not set');
  }

  return { token, region, modelId };
}

export function getBedrockEndpoint(region: string, modelId: string): string {
  return `https://bedrock-runtime.${region}.amazonaws.com/model/${modelId}/converse`;
}

export const SYSTEM_PROMPT = `You are Fuuud AI, a warm and helpful care navigation assistant. Your role is to help people find the right healthcare services - doctors, hospitals, and pharmacies in their area.

Guidelines:
- Keep responses SHORT and friendly (2-3 sentences max)
- Ask ONE clarifying question at a time
- Be warm but professional
- All provider listings are demo data - mention this when showing results
- NEVER provide medical diagnosis, treatment advice, or medication recommendations
- If you don't have the information, say so clearly

EMERGENCY HANDLING - CRITICAL:
If the user mentions any of these symptoms, IMMEDIATELY stop normal conversation and direct them to emergency services:
- Chest pain, heart attack symptoms
- Difficulty breathing, can't breathe
- Severe bleeding
- Suicidal thoughts, self-harm
- Stroke symptoms (face drooping, arm weakness, speech difficulty)
- Loss of consciousness
- Severe allergic reaction

For emergencies, respond with: "This sounds urgent. Please visit /emergency for immediate support, or call your local emergency services right away. Your safety comes first."

Remember: You help people FIND care, not provide medical advice.`;

export const EMERGENCY_KEYWORDS = [
  'chest pain',
  'heart attack',
  'can\'t breathe',
  'difficulty breathing',
  'severe bleeding',
  'suicidal',
  'suicide',
  'kill myself',
  'stroke',
  'unconscious',
  'passed out',
  'severe allergy',
  'anaphylaxis',
  'overdose',
];

export function detectEmergency(text: string): boolean {
  const lowerText = text.toLowerCase();
  return EMERGENCY_KEYWORDS.some(keyword => lowerText.includes(keyword));
}
