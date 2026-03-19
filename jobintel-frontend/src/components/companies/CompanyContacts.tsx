import { useQuery } from "@tanstack/react-query";
import { getCompanyContacts } from "../../services/api/companies";
import { Mail, Phone, Linkedin, ExternalLink } from "lucide-react";

interface CompanyContactsProps {
  companyId: string;
}

interface Contact {
  id: string;
  full_name?: string;
  title?: string;
  email?: string;
  phone?: string;
  linkedin_url?: string;
  department?: string;
  seniority?: string;
}

export function CompanyContacts({ companyId }: CompanyContactsProps) {
  const {
    data: contactsResponse,
    isLoading,
    isError,
  } = useQuery<any>({
    queryKey: ["companyContacts", companyId],
    queryFn: () => getCompanyContacts(companyId),
    enabled: !!companyId,
  });

  const contacts = contactsResponse?.items || [];

  // Filter out completely empty contacts - only hide those with no data at all
  const validContacts = contacts.filter((contact: Contact) => {
    // Hide if no name AND no other useful data
    const hasAnyData =
      contact.full_name ||
      contact.email ||
      contact.phone ||
      contact.linkedin_url ||
      contact.title ||
      contact.department ||
      contact.seniority;
    return hasAnyData;
  });

  if (isLoading) {
    return (
      <div className="text-center py-6 text-text-secondary animate-pulse">
        Loading contacts...
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center py-6 text-text-error">
        Failed to load contacts
      </div>
    );
  }

  if (contacts.length === 0) {
    return (
      <div className="text-center py-6 text-text-secondary bg-bg-base rounded-md border border-border-subtle border-dashed">
        No contacts found
      </div>
    );
  }

  if (validContacts.length === 0) {
    return (
      <div className="text-center py-6 text-text-secondary bg-bg-base rounded-md border border-border-subtle border-dashed">
        No valid contacts found
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {validContacts.map((contact: Contact) => (
        <div
          key={contact.id}
          className="p-4 rounded-md border border-border-subtle bg-bg-base hover:border-accent-primary/50 transition-colors"
        >
          {/* Name and Title */}
          <div className="mb-2">
            <h4 className="font-medium text-text-primary">
              {contact.full_name || "Unknown Name"}
            </h4>
            {contact.title && (
              <p className="text-xs text-text-secondary">{contact.title}</p>
            )}
            {contact.department && (
              <p className="text-xs text-text-secondary">
                {contact.department}
              </p>
            )}
            {contact.seniority && (
              <span className="text-xs inline-block mt-1 px-2 py-1 rounded bg-bg-elevated text-text-secondary border border-border-subtle">
                {contact.seniority}
              </span>
            )}
          </div>

          {/* Contact Links */}
          <div className="flex flex-wrap gap-2 mt-3">
            {contact.email && (
              <a
                href={`mailto:${contact.email}`}
                className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs text-text-secondary hover:text-accent-primary hover:bg-bg-elevated transition-colors border border-border-subtle"
                title={contact.email}
              >
                <Mail size={14} />
                <span className="truncate max-w-[120px]">{contact.email}</span>
              </a>
            )}

            {contact.phone && (
              <a
                href={`tel:${contact.phone}`}
                className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs text-text-secondary hover:text-accent-primary hover:bg-bg-elevated transition-colors border border-border-subtle"
                title={contact.phone}
              >
                <Phone size={14} />
                <span className="truncate max-w-[120px]">{contact.phone}</span>
              </a>
            )}

            {contact.linkedin_url && (
              <a
                href={contact.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2 py-1 rounded text-xs text-blue-500 hover:text-blue-600 hover:bg-bg-elevated transition-colors border border-blue-200/50"
                title="LinkedIn Profile"
              >
                <Linkedin size={14} />
                LinkedIn
                <ExternalLink size={12} />
              </a>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
