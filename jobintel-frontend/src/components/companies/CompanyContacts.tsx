import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { findCompanyContacts } from "../../services/api/companies";
import { Loader2, Users, Mail, Linkedin, Check } from "lucide-react";

interface CompanyContactsProps {
    company: any;
}

export function CompanyContacts({ company }: CompanyContactsProps) {
    const [contacts, setContacts] = useState<any[]>([]);
    const [copiedEmail, setCopiedEmail] = useState<string | null>(null);

    const mutation = useMutation({
        mutationFn: () => findCompanyContacts(company.id),
        onSuccess: (data) => {
            if (data?.contacts) {
                setContacts(data.contacts);
            }
        }
    });

    const handleCopyEmail = (email: string) => {
        if (!email) return;
        navigator.clipboard.writeText(email);
        setCopiedEmail(email);
        setTimeout(() => setCopiedEmail(null), 2000);
    };

    if (mutation.isError) {
        return (
            <div className="text-center py-4 text-text-error text-sm mt-4 bg-bg-base border border-border-subtle rounded-md">
                Failed to fetch contacts.
            </div>
        );
    }

    if (mutation.isPending) {
        return (
            <div className="flex flex-col items-center justify-center py-8 text-text-secondary mt-4 bg-bg-base border border-border-subtle rounded-md border-dashed">
                <Loader2 className="animate-spin mb-3 text-accent-primary" size={28} />
                <span className="text-sm font-medium">Searching contacts...</span>
            </div>
        );
    }

    if (contacts.length > 0) {
        return (
            <div className="mt-6 mb-6">
                <div className="flex items-center justify-between mb-3">
                    <h3 className="text-[16px] font-semibold text-text-primary flex items-center gap-2">
                        <Users size={18} />
                        Key Contacts
                    </h3>
                    <span className="text-xs font-medium bg-bg-elevated px-2 py-0.5 rounded-full border border-border-subtle">
                        {contacts.length} found
                    </span>
                </div>

                <div className="overflow-hidden border border-border-subtle rounded-lg bg-bg-base">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="bg-bg-elevated border-b border-border-subtle">
                                <th className="py-2 px-3 text-xs font-medium text-text-secondary uppercase">Name</th>
                                <th className="py-2 px-3 text-xs font-medium text-text-secondary uppercase">Title</th>
                                <th className="py-2 px-3 text-xs font-medium text-text-secondary uppercase text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border-subtle">
                            {contacts.map((contact: any) => (
                                <tr key={contact.id || contact.email || contact.full_name} className="hover:bg-bg-surface transition-colors">
                                    <td className="py-2.5 px-3">
                                        <div className="font-medium text-sm text-text-primary">{contact.full_name}</div>
                                    </td>
                                    <td className="py-2.5 px-3">
                                        <div className="text-xs text-text-secondary">{contact.title || contact.department || 'Unknown Role'}</div>
                                    </td>
                                    <td className="py-2.5 px-3">
                                        <div className="flex items-center justify-end gap-2">
                                            {contact.email && (
                                                <button
                                                    onClick={() => handleCopyEmail(contact.email)}
                                                    className="p-1.5 rounded bg-bg-elevated border border-border-subtle text-text-secondary hover:text-text-primary hover:border-accent-primary transition-colors"
                                                    title="Copy Email"
                                                >
                                                    {copiedEmail === contact.email ? <Check size={14} className="text-green-500" /> : <Mail size={14} />}
                                                </button>
                                            )}
                                            {contact.linkedin_url && (
                                                <a
                                                    href={contact.linkedin_url}
                                                    target="_blank"
                                                    rel="noreferrer"
                                                    className="p-1.5 rounded bg-[#0A66C2]/10 border border-[#0A66C2]/20 text-[#0A66C2] hover:bg-[#0A66C2]/20 transition-colors"
                                                    title="Open LinkedIn"
                                                >
                                                    <Linkedin size={14} />
                                                </a>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        );
    }

    return (
        <div className="mt-6 mb-6 py-8 px-4 bg-bg-base border border-border-subtle rounded-lg flex flex-col items-center justify-center gap-3 border-dashed hover:border-accent-primary/50 transition-colors">
            <div className="h-10 w-10 rounded-full bg-accent-primary/10 flex items-center justify-center mb-1">
                <Users className="text-accent-primary" size={20} />
            </div>
            <p className="text-sm text-text-secondary text-center max-w-xs">
                Discover HR, Talent, and Engineering leadership contacts for this organization.
            </p>
            <button
                onClick={() => mutation.mutate()}
                className="mt-2 flex items-center gap-2 px-4 py-2 bg-bg-elevated border border-border-subtle hover:border-accent-primary hover:text-accent-primary text-text-primary rounded-md text-sm font-medium transition-colors shadow-sm"
            >
                <Users size={16} />
                Find Contacts
            </button>
        </div>
    );
}
