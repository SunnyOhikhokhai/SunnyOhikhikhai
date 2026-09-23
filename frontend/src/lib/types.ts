export interface CouncilRef {
  slug: string;
  name: string;
  short_name: string;
}

export interface Council extends CouncilRef {
  id: number;
  headquarters: string | null;
  summary: string;
  description: string;
  image_url: string | null;
  wards: string[];
  member_count?: number;
  latest_update?: { title: string; slug: string; published_at: string } | null;
}

export interface Category {
  slug: string;
  name: string;
  description?: string;
}

export type VerificationStatus = "unverified" | "pending_review" | "verified" | "disputed";

export interface RecordCard {
  id: number;
  slug: string;
  title: string;
  category: Category;
  area_council: CouncilRef | null;
  location: string | null;
  year: number | null;
  record_date: string | null;
  summary: string;
  verification_status: VerificationStatus;
  is_featured: boolean;
  is_demo: boolean;
  image: { url: string; alt: string } | null;
  source_count: number;
  published_at: string | null;
}

export interface Source {
  title: string;
  publisher: string | null;
  url: string | null;
  published_on: string | null;
  notes: string | null;
}

export interface RecordDetail extends RecordCard {
  description: string;
  verification_note: string | null;
  images: { url: string; alt: string; caption: string | null; credit: string | null }[];
  documents: { title: string; url: string; file_type: string | null }[];
  sources: Source[];
  view_count: number;
  updated_at: string;
  related?: RecordCard[];
  status?: string;
}

export type ContentLabel = "verified_information" | "announcement" | "opinion" | "historical_record" | "update";

export interface NewsCard {
  id: number;
  slug: string;
  title: string;
  excerpt: string;
  category: Category;
  area_council: CouncilRef | null;
  content_label: ContentLabel;
  image_url: string | null;
  image_alt: string | null;
  author_name: string;
  is_demo: boolean;
  is_featured: boolean;
  published_at: string | null;
}

export interface NewsDetail extends NewsCard {
  body: string;
  source_note: string | null;
  updated_at: string;
  related?: NewsCard[];
  status?: string;
  view_count?: number;
}

export interface EventItem {
  id: number;
  slug: string;
  title: string;
  summary: string;
  description?: string;
  starts_at: string;
  ends_at: string | null;
  location: string;
  area_council: CouncilRef | null;
  image_url: string | null;
  organizer: string;
  registration_open: boolean;
  capacity: number | null;
  status: "draft" | "published" | "cancelled" | "archived";
  is_demo: boolean;
  registered_count?: number;
  spots_left?: number | null;
  is_registered?: boolean;
  view_count?: number;
}

export interface Author {
  id?: number;
  name: string;
  is_team: boolean;
}

export interface DiscussionItem {
  id: number;
  title: string;
  body: string;
  category: Category;
  area_council: CouncilRef | null;
  author: Author;
  status: string;
  is_pinned: boolean;
  is_locked: boolean;
  is_demo: boolean;
  comment_count: number;
  reaction_count: number;
  liked: boolean | null;
  created_at: string;
  last_activity_at: string;
}

export interface CommentItem {
  id: number;
  parent_id: number | null;
  author: Author;
  body: string;
  status: string;
  reaction_count: number;
  liked: boolean | null;
  created_at: string;
}

export interface NotificationItem {
  id: number;
  type: "announcement" | "event" | "community" | "account" | "council_update";
  title: string;
  body: string;
  link: string | null;
  read: boolean;
  created_at: string;
}

export interface Announcement {
  id: number;
  title: string;
  body: string;
  link_url: string | null;
  area_council: CouncilRef | null;
  priority: "normal" | "important";
  status: string;
  publish_at: string | null;
  expires_at: string | null;
  is_demo: boolean;
  created_at: string;
}

export interface Me {
  id: number;
  full_name: string;
  first_name: string;
  email: string;
  phone: string | null;
  email_verified: boolean;
  phone_verified: boolean;
  status: string;
  created_at: string;
  area_council: CouncilRef | null;
  profile: { display_name: string | null; bio: string | null; avatar_url: string | null; ward: string | null; community: string | null };
  admin: { role: string; role_name: string; area_council: CouncilRef | null; permissions: string[] } | null;
}

export interface Preferences {
  in_app_announcements: boolean;
  in_app_events: boolean;
  in_app_community: boolean;
  in_app_council_updates: boolean;
  email_announcements: boolean;
  email_events: boolean;
  email_community: boolean;
  sms_announcements: boolean;
  sms_events: boolean;
  sms_enabled: boolean;
}

export interface Meta {
  area_councils: CouncilRef[];
  project_categories: Category[];
  news_categories: Category[];
  discussion_categories: Category[];
  record_years: number[];
}

export interface PrincipalProfile {
  name: string;
  title: string;
  tagline: string;
  summary: string;
  biography: string;
  photo_url: string | null;
  photo_alt: string | null;
  timeline: { year: string; title: string; description: string; source: string }[];
  gallery: { url: string; alt: string; caption: string }[];
  links: { label: string; url: string }[];
  updated_at: string;
}
