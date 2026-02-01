export interface User {
  id: number;
  username: string;
  display_name: string | null;
  email: string | null;
  role: string;
}

export interface UserProfile extends User {
  avatar_url: string | null;
  created_at: string;
}

export enum MediaType {
  Movie = "movie",
  Series = "series",
}

export enum ServiceType {
  Jellyfin = "jellyfin",
  Plex = "plex",
  Radarr = "radarr",
  Sonarr = "sonarr",
  Seerr = "seerr",
  General = "general",
  Notifications = "notifications",
}

export type LibraryType = {
  serviceType: ServiceType;
  mediaType: MediaType;
  libName: string;
};
