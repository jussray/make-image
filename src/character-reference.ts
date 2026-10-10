/** Privacy-first character reference contract. No biometric identity or face embeddings. */
export type CharacterReference = Readonly<{
  projectId: string;
  characterId: string;
  assetId: string;
  assetVersion: string;
  consentScope: "fictional-character" | "authorized-adult-likeness";
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
  const matches = references.filter((ref) =>
    ref.projectId === request.projectId &&
    ref.characterId === request.characterId &&
    ref.approvedFor.includes(request.output) &&
    ref.assetId.trim().length > 0 &&
    ref.assetVersion.trim().length > 0
  );
  // Ambiguous reference selection fails closed.
  return matches.length === 1 ? matches[0] : null;
}
