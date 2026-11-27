import indiaLocations from "../../config/india_locations.json";
import categoriesData from "../../config/categories.json";

export function slugify(text: string): string {
  return text
    .toLowerCase()
    .replace(/&/g, "and")
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function deterministicHash(seed: string): number {
  let h = 0;
  for (let i = 0; i < seed.length; i++) {
    h = (h * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return h;
}

export function resolveLocalParams(stateSlug: string, citySlug: string, catSlug: string) {
  const stateObj = (indiaLocations as any[]).find(
    (s) => s.id === stateSlug || slugify(s.name) === stateSlug
  );
  if (!stateObj) return null;

  const cityObj = (stateObj.cities as any[]).find(
    (c) => c.id === citySlug || slugify(c.name) === citySlug
  );
  if (!cityObj) return null;

  const catObj = (categoriesData as any[]).find(
    (cat) => cat.id === catSlug || slugify(cat.name) === catSlug
  );
  if (!catObj) return null;

  const seed = `${stateObj.id}:${cityObj.id}:${catObj.id}`;
  const h = deterministicHash(seed);

  // Quality gate: Batch 1 indexes Odisha cities × top 20 categories
  const top20CatIds = new Set((categoriesData as any[]).slice(0, 20).map((c) => c.id));
  const isBatch1Indexable = stateObj.id === "odisha" && top20CatIds.has(catObj.id);

  const approxCount = 35 + (h % 140);
  const noWebsitePct = 42 + (h % 31); // 42% - 72%
  const avgRating = (3.8 + ((h % 8) * 0.1)).toFixed(1);

  const maskedSamples = [
    {
      maskedName: `K***** ${catObj.name.split("&")[0].trim()}`,
      locality: `${cityObj.name} Central`,
      hasWebsite: "No",
      rating: `${avgRating} ★`,
      score: 90,
    },
    {
      maskedName: `S**** ${catObj.name.split("&")[0].trim()} Care`,
      locality: `Main Road, ${cityObj.name}`,
      hasWebsite: "No",
      rating: `${(Number(avgRating) - 0.2).toFixed(1)} ★`,
      score: 85,
    },
    {
      maskedName: `A*** ${catObj.name.split("&")[0].trim()} Hub`,
      locality: `${cityObj.district} Area`,
      hasWebsite: "Yes",
      rating: "4.4 ★",
      score: 60,
    },
  ];

  const relatedCities = (stateObj.cities as any[])
    .filter((c) => c.id !== cityObj.id)
    .slice(0, 6)
    .map((c) => ({ name: c.name, slug: slugify(c.name) }));

  const relatedCategories = (categoriesData as any[])
    .filter((c) => c.id !== catObj.id)
    .slice(0, 6)
    .map((c) => ({ name: c.name, slug: slugify(c.name) }));

  return {
    state: stateObj.name as string,
    stateSlug: slugify(stateObj.name),
    city: cityObj.name as string,
    citySlug: slugify(cityObj.name),
    district: cityObj.district as string,
    category: catObj.name as string,
    categorySlug: slugify(catObj.name),
    group: (catObj.group || "Business Services") as string,
    isIndexable: isBatch1Indexable,
    stats: { approxCount, noWebsitePct, avgRating },
    maskedSamples,
    relatedCities,
    relatedCategories,
  };
}

export function getBatch1LocalUrls(): Array<{ state: string; city: string; category: string }> {
  const odisha = (indiaLocations as any[]).find((s) => s.id === "odisha");
  if (!odisha) return [];
  const topCities = (odisha.cities as any[]).slice(0, 10);
  const topCats = (categoriesData as any[]).slice(0, 10);
  const paths: Array<{ state: string; city: string; category: string }> = [];
  for (const c of topCities) {
    for (const cat of topCats) {
      paths.push({
        state: "odisha",
        city: slugify(c.name),
        category: slugify(cat.name),
      });
    }
  }
  return paths;
}
