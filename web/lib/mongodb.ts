import { MongoClient } from "mongodb";

declare global {
  var _mongoClientPromise: Promise<MongoClient> | undefined;
}

function getMongoConfig() {
  const mongoUri = process.env.MONGODB_URI;
  const mongoDatabaseName = process.env.MONGODB_DB ?? process.env.MONGO_DB_NAME;

  if (!mongoUri) {
    throw new Error("Missing MONGODB_URI in environment.");
  }

  if (!mongoDatabaseName) {
    throw new Error(
      "Missing MONGODB_DB in environment. Set MONGODB_DB or MONGO_DB_NAME.",
    );
  }

  return {
    mongoUri,
    mongoDatabaseName,
  };
}

function getClientPromise(mongoUri: string) {
  if (!global._mongoClientPromise) {
    const client = new MongoClient(mongoUri, {
      serverSelectionTimeoutMS: 5000,
    });
    global._mongoClientPromise = client.connect();
  }

  return global._mongoClientPromise;
}

export async function getDatabase() {
  const { mongoUri, mongoDatabaseName } = getMongoConfig();

  try {
    const connectedClient = await getClientPromise(mongoUri);
    return connectedClient.db(mongoDatabaseName);
  } catch (error) {
    global._mongoClientPromise = undefined;
    throw error;
  }
}
