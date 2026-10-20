/** Character asset lookup only; never authenticates real-person consent. */
export type CharacterReference = Readonly<{
  projectId: string;
  characterId: string;
  assetId: string;
  assetVersion: string;
  consentScope: "fictional-character" | "authorized-adult-likeness";
  consentEvidenceId?: string;
  approvedFor: readonly ("image" | "video")[];
}>;
export type CharacterReferenceRequest = Readonly<{
  projectId: string;
  characterId: string;
  output: "image" | "video";
}>;
export function selectCharacterReference(
  references: readonly CharacterReference[],
  request: CharacterReferenceRequest,
): CharacterReference | null {
  if (!request || ![request.projectId, request.characterId].every(v => typeof v === 'string' && v.trim()) ||
      !['image', 'video'].includes(request.output) || !Array.isArray(references)) return null;
  const matches = references.filter((ref) =>
    ref && typeof ref === 'object' &&
    ref.projectId === request.projectId && ref.characterId === request.characterId &&
    typeof ref.assetId === 'string' && ref.assetId.trim().length > 0 &&
    typeof ref.assetVersion === 'string' && ref.assetVersion.trim().length > 0 &&
    Array.isArray(ref.approvedFor) && ref.approvedFor.includes(request.output) &&
    (ref.consentScope === 'fictional-character' ||
      (ref.consentScope === 'authorized-adult-likeness' &&
       typeof ref.consentEvidenceId === 'string' && ref.consentEvidenceId.trim().length > 0))
  );
  // This verifies consent-record presence, not its authenticity.
  // Ambiguous reference selection fails closed.
  return matches.length === 1 ? matches[0] : null;
}
