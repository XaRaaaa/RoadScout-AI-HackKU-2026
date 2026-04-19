import { getDatabase } from "@/lib/mongodb";

export type StoredPhoto = {
  _id: string;
  filename: string;
  contentType: string;
  uploadedAt: string;
  size: number;
  analysisStatus?: string;
  analysisNote?: string;
  analysisSummary?: string;
  authorityToReport?: string;
  classifier?: {
    modelName: string;
    imageSize: number;
    prediction: string;
    confidence: number;
    severity: string;
    recommendedAction: string;
  };
  address?: string;
  location?: {
    latitude: number;
    longitude: number;
    accuracyMeters?: number;
  };
};

export async function getPhotoCollection() {
  const db = await getDatabase();
  return db.collection("photos");
}
