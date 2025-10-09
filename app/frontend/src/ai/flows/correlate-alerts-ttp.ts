// This file is machine-generated - edit at your own risk.
'use server';
/**
 * @fileOverview Correlates alerts based on `ttp_id` to known threats and MITRE ATT&CK techniques.
 *
 * - correlateAlertsTTP - A function that correlates alerts based on TTP IDs.
 * - CorrelateAlertsTTPInput - The input type for the correlateAlertsTTP function.
 * - CorrelateAlertsTTPOutput - The return type for the correlateAlertsTTP function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const CorrelateAlertsTTPInputSchema = z.object({
  ttp_id: z.string().describe('The TTP ID to correlate with known threats and MITRE ATT&CK techniques.'),
  alertDescription: z.string().optional().describe('Optional alert description to provide additional context.'),
});
export type CorrelateAlertsTTPInput = z.infer<typeof CorrelateAlertsTTPInputSchema>;

const CorrelateAlertsTTPOutputSchema = z.object({
  threatName: z.string().describe('The name of the identified threat.'),
  mitreTechniques: z.array(z.string()).describe('An array of MITRE ATT&CK techniques associated with the TTP ID.'),
  impactAssessment: z.string().describe('An assessment of the potential impact of the alerts.'),
});
export type CorrelateAlertsTTPOutput = z.infer<typeof CorrelateAlertsTTPOutputSchema>;

export async function correlateAlertsTTP(input: CorrelateAlertsTTPInput): Promise<CorrelateAlertsTTPOutput> {
  return correlateAlertsTTPFlow(input);
}

const correlateAlertsTTPPrompt = ai.definePrompt({
  name: 'correlateAlertsTTPPrompt',
  input: {schema: CorrelateAlertsTTPInputSchema},
  output: {schema: CorrelateAlertsTTPOutputSchema},
  prompt: `You are a security analyst expert at correlating alerts to known threats and MITRE ATT&CK techniques.

  Given the following TTP ID and alert description (if available), identify the threat name, associated MITRE ATT&CK techniques, and assess the potential impact of the alerts.

  TTP ID: {{{ttp_id}}}
  {{#if alertDescription}}
  Alert Description: {{{alertDescription}}}
  {{/if}}

  Threat Name:
  MITRE ATT&CK Techniques:
  Impact Assessment:`,
});

const correlateAlertsTTPFlow = ai.defineFlow(
  {
    name: 'correlateAlertsTTPFlow',
    inputSchema: CorrelateAlertsTTPInputSchema,
    outputSchema: CorrelateAlertsTTPOutputSchema,
  },
  async input => {
    const {output} = await correlateAlertsTTPPrompt(input);
    return output!;
  }
);
