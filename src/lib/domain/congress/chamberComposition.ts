export type Party = 'democratic' | 'republican' | 'independent';
export type MajorityParty = Party | 'tie';

export type ChamberCompositionInput = {
	democraticSeats: number;
	republicanSeats: number;
	independentSeats?: number;
};

export type ChamberComposition = {
	totalSeats: number;
	majorityParty: MajorityParty;
	majorityMargin: number;
	partyShares: Record<Party, number>;
	isPluralityScaffoldResult: boolean;
};

function safeSeatCount(value: number | undefined): number {
	if (value === undefined) return 0;
	if (!Number.isFinite(value) || value < 0) {
		throw new Error('Seat counts must be finite, non-negative numbers.');
	}
	return value;
}

export function deriveChamberComposition(input: ChamberCompositionInput): ChamberComposition {
	const seats: Record<Party, number> = {
		democratic: safeSeatCount(input.democraticSeats),
		republican: safeSeatCount(input.republicanSeats),
		independent: safeSeatCount(input.independentSeats)
	};
	const totalSeats = seats.democratic + seats.republican + seats.independent;
	const ordered = Object.entries(seats).sort((a, b) => b[1] - a[1]) as Array<[Party, number]>;
	const [leader, leaderSeats] = ordered[0];
	const runnerUpSeats = ordered[1][1];
	const tiedForLead = ordered.filter(([, count]) => count === leaderSeats).length > 1;
	const majorityParty: MajorityParty = tiedForLead ? 'tie' : leader;

	return {
		totalSeats,
		majorityParty,
		majorityMargin: tiedForLead ? 0 : leaderSeats - runnerUpSeats,
		partyShares: {
			democratic: totalSeats === 0 ? 0 : seats.democratic / totalSeats,
			republican: totalSeats === 0 ? 0 : seats.republican / totalSeats,
			independent: totalSeats === 0 ? 0 : seats.independent / totalSeats
		},
		// Independent plurality is a scaffold simplification, not a caucus-aware rule.
		isPluralityScaffoldResult: majorityParty === 'independent'
	};
}
