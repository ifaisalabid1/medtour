/** The signed-in staff member, as the admin layout passes it to pages. */
export interface AdminUser {
  id: string;
  name: string;
  email: string;
  isAdmin: boolean;
}
