import { NextRequest, NextResponse } from 'next/server';
import { validateBedrockConfig, getBedrockEndpoint, SYSTEM_PROMPT, detectEmergency, BedrockConfigError } from '@/lib/bedrock';
import { doctors, hospitals, pharmacies } from '@/data/mock';

// Rate limiting: simple in-memory store (use Redis in production)
const rateLimitStore = new Map<string, { count: number; resetAt: number }>();
const RATE_LIMIT = 20; // requests per window
const RATE_WINDOW = 60 * 1000; // 1 minute

function checkRateLimit(identifier: string): boolean {
  const now = Date.now();
  const record = rateLimitStore.get(identifier);

  if (!record || now > record.resetAt) {
    rateLimitStore.set(identifier, { count: 1, resetAt: now + RATE_WINDOW });
    return true;
  }

  if (record.count >= RATE_LIMIT) {
    return false;
  }

  record.count++;
  return true;
}

// Tool implementations
function searchDoctors(specialty?: string, location?: string) {
  let results = [...doctors];

  if (specialty) {
    const specLower = specialty.toLowerCase();
    results = results.filter(d => d.specialty.toLowerCase().includes(specLower));
  }

  if (location) {
    const locLower = location.toLowerCase();
    results = results.filter(d => d.location.toLowerCase().includes(locLower));
  }

  return results.map(d => ({
    id: d.id,
    name: d.name,
    specialty: d.specialty,
    location: d.location,
    fee: `₦${d.fee.toLocaleString()}`,
    nextAvailable: d.next,
    rating: d.rating,
    experience: `${d.experience} years`,
    bio: d.bio,
  }));
}

function findHospitals(location?: string, emergencyOnly?: boolean) {
  let results = [...hospitals];

  if (location) {
    const locLower = location.toLowerCase();
    results = results.filter(h => h.location.toLowerCase().includes(locLower));
  }

  if (emergencyOnly) {
    results = results.filter(h => h.emergency);
  }

  return results.map(h => ({
    id: h.id,
    name: h.name,
    location: h.location,
    distance: h.distance,
    eta: h.eta,
    type: h.type,
    hasEmergency: h.emergency,
    open: h.open,
    services: h.services,
  }));
}

function findPharmacies(location?: string) {
  let results = [...pharmacies];

  if (location) {
    const locLower = location.toLowerCase();
    results = results.filter(p => p.location.toLowerCase().includes(locLower));
  }

  return results.map(p => ({
    id: p.id,
    name: p.name,
    location: p.location,
    distance: p.distance,
    open: p.open,
    verified: p.verified,
  }));
}

// Tool definitions for Bedrock
const tools = [
  {
    toolSpec: {
      name: 'search_doctors',
      description: 'Search for doctors by specialty and/or location. Returns a list of available doctors with their details.',
      inputSchema: {
        json: {
          type: 'object',
          properties: {
            specialty: {
              type: 'string',
              description: 'Medical specialty (e.g., Dermatology, Pediatrics, General Physician, Cardiology)',
            },
            location: {
              type: 'string',
              description: 'City or area name (e.g., Awka, Nnewi)',
            },
          },
        },
      },
    },
  },
  {
    toolSpec: {
      name: 'find_hospitals',
      description: 'Find hospitals and medical facilities. Can filter by location and emergency services availability.',
      inputSchema: {
        json: {
          type: 'object',
          properties: {
            location: {
              type: 'string',
              description: 'City or area to search in',
            },
            emergencyOnly: {
              type: 'boolean',
              description: 'Set to true to only show hospitals with emergency units',
            },
          },
        },
      },
    },
  },
  {
    toolSpec: {
      name: 'find_pharmacies',
      description: 'Find pharmacies in a given area.',
      inputSchema: {
        json: {
          type: 'object',
          properties: {
            location: {
              type: 'string',
              description: 'City or area to search in',
            },
          },
        },
      },
    },
  },
];

async function callBedrock(messages: any[], config: any) {
  const endpoint = getBedrockEndpoint(config.region, config.modelId);

  console.log('[Bedrock Request]');
  console.log('- Endpoint:', endpoint);
  console.log('- Messages count:', messages.length);
  console.log('- First message role:', messages[0]?.role);

  const requestBody = {
    system: [{ text: SYSTEM_PROMPT }],
    messages,
    inferenceConfig: {
      maxTokens: 1000,
      temperature: 0.7,
    },
    toolConfig: { tools },
  };

  console.log('- Request body:', JSON.stringify(requestBody, null, 2).substring(0, 500) + '...');

  const response = await fetch(endpoint, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${config.token}`,
    },
    body: JSON.stringify(requestBody),
  });

  console.log('[Bedrock Response]');
  console.log('- Status:', response.status, response.statusText);

  if (!response.ok) {
    const errorText = await response.text();
    console.error('- Error body:', errorText);

    // Parse error details if JSON
    let errorDetails = errorText;
    try {
      const errorJson = JSON.parse(errorText);
      errorDetails = JSON.stringify(errorJson, null, 2);
    } catch {}

    throw new Error(`Bedrock API error: ${response.status} - ${errorText.substring(0, 200)}`);
  }

  const data = await response.json();
  console.log('- Response:', JSON.stringify(data, null, 2).substring(0, 300) + '...');
  return data;
}

function executeToolCall(toolName: string, toolInput: any) {
  switch (toolName) {
    case 'search_doctors':
      return searchDoctors(toolInput.specialty, toolInput.location);
    case 'find_hospitals':
      return findHospitals(toolInput.location, toolInput.emergencyOnly);
    case 'find_pharmacies':
      return findPharmacies(toolInput.location);
    default:
      return { error: 'Unknown tool' };
  }
}

export async function POST(request: NextRequest) {
  try {
    // Validate environment configuration
    let config;
    try {
      config = validateBedrockConfig();
    } catch (error) {
      if (error instanceof BedrockConfigError) {
        return NextResponse.json(
          { error: 'Configuration error. Please set up Bedrock environment variables.' },
          { status: 500 }
        );
      }
      throw error;
    }

    // Rate limiting
    const ip = request.headers.get('x-forwarded-for')?.split(',')[0] || 'unknown';
    if (!checkRateLimit(ip)) {
      return NextResponse.json(
        { error: 'Too many requests. Please wait a moment and try again.' },
        { status: 429 }
      );
    }

    // Parse request body
    const body = await request.json();
    const { messages } = body;

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json(
        { error: 'Invalid request format' },
        { status: 400 }
      );
    }

    // Check message length limits
    for (const msg of messages) {
      if (msg.content?.[0]?.text && msg.content[0].text.length > 2000) {
        return NextResponse.json(
          { error: 'Message too long. Please keep messages under 2000 characters.' },
          { status: 400 }
        );
      }
    }

    // Emergency detection on user messages
    const lastUserMessage = [...messages].reverse().find(m => m.role === 'user');
    if (lastUserMessage?.content?.[0]?.text) {
      const userText = lastUserMessage.content[0].text;
      if (detectEmergency(userText)) {
        return NextResponse.json({
          role: 'assistant',
          content: [
            {
              text: 'This sounds urgent. Please visit /emergency for immediate support, or call your local emergency services right away. Your safety comes first.',
            },
          ],
          emergencyDetected: true,
        });
      }
    }

    // Conversation loop with tool use (max 4 iterations)
    let conversationMessages = [...messages];
    let iterations = 0;
    const MAX_ITERATIONS = 4;

    while (iterations < MAX_ITERATIONS) {
      iterations++;

      const bedrockResponse = await callBedrock(conversationMessages, config);

      // Check stop reason
      if (bedrockResponse.stopReason === 'end_turn') {
        // Model finished with a text response
        return NextResponse.json({
          role: 'assistant',
          content: bedrockResponse.output.message.content,
        });
      }

      if (bedrockResponse.stopReason === 'tool_use') {
        // Model wants to use a tool
        const assistantMessage = bedrockResponse.output.message;
        conversationMessages.push(assistantMessage);

        // Execute all tool calls
        const toolResults: any[] = [];
        for (const contentBlock of assistantMessage.content) {
          if (contentBlock.toolUse) {
            const { toolUseId, name, input } = contentBlock.toolUse;
            const result = executeToolCall(name, input);
            toolResults.push({
              toolResult: {
                toolUseId,
                content: [{ json: result }],
              },
            });
          }
        }

        // Add tool results to conversation
        conversationMessages.push({
          role: 'user',
          content: toolResults,
        });

        // Continue loop to get final response
        continue;
      }

      // Unexpected stop reason
      return NextResponse.json(
        { error: 'Unexpected response from AI. Please try again.' },
        { status: 500 }
      );
    }

    // Max iterations reached
    return NextResponse.json(
      { error: 'I need a moment to gather my thoughts. Could you try asking again?' },
      { status: 500 }
    );

  } catch (error) {
    console.error('Agent API error:', error);

    // Return a safe error code for development debugging
    let errorCode = 'UNKNOWN_ERROR';
    let userMessage = 'I lost my train of thought. Shall we try again?';

    if (error instanceof Error) {
      if (error.message.includes('403')) {
        errorCode = 'BEDROCK_ACCESS_DENIED';
      } else if (error.message.includes('404')) {
        errorCode = 'BEDROCK_MODEL_NOT_FOUND';
      } else if (error.message.includes('ValidationException')) {
        errorCode = 'BEDROCK_VALIDATION_ERROR';
      } else if (error.message.includes('Configuration error')) {
        errorCode = 'ENV_CONFIG_MISSING';
      }
    }

    return NextResponse.json(
      {
        error: userMessage,
        errorCode, // Safe to expose in development
      },
      { status: 500 }
    );
  }
}
