// Start elke ochtend en op de vrijdagavond (nieuwe folder vanaf 17.00 uur) het uitlezen van de Nettorama-folder.
export default async () => {
  const basis = Netlify.env.get('URL') || 'https://boodschappenvergelijk.nl';
  await fetch(`${basis}/.netlify/functions/nettorama-folder-background`, { method: 'POST' }).catch(() => {});
};
export const config = { schedule: '7 3,18 * * *' };
