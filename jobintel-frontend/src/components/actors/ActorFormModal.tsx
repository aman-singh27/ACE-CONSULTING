import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { createActor, updateActor } from "../../services/api/actors";
import { Button } from "../ui/Button";
import { X } from "lucide-react";
import type { ActorItem } from "./ActorTable";

interface ActorFormModalProps {
    actor?: ActorItem | null;
    onClose: () => void;
}

export function ActorFormModal({ actor, onClose }: ActorFormModalProps) {
    const queryClient = useQueryClient();
    const isEditing = !!actor;

    const [formData, setFormData] = useState({
        actor_name: actor?.actor_name || "",
        actor_id: actor?.actor_id || "",
        platform: actor?.platform || "",
        domain: actor?.domain || "",
        normalizer_key: actor?.normalizer_key || "",
        frequency_days: actor?.frequency_days || 1,
        apify_input_template: actor?.apify_input_template ? JSON.stringify(actor.apify_input_template, null, 2) : "{}",
    });

    const [error, setError] = useState<string | null>(null);

    const mutation = useMutation({
        mutationFn: async () => {
            let inputTemplate = {};
            try {
                inputTemplate = JSON.parse(formData.apify_input_template);
            } catch {
                throw new Error("Invalid JSON in input template");
            }

            const payload = {
                ...formData,
                frequency_days: Number(formData.frequency_days),
                apify_input_template: inputTemplate,
            };

            if (isEditing && actor) {
                return updateActor(actor.id, payload);
            }
            return createActor(payload);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["actors"] });
            onClose();
        },
        onError: (err: any) => {
            setError(err?.message || "Failed to save actor");
        },
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);
        mutation.mutate();
    };

    const handleChange = (field: string, value: string | number) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* Backdrop */}
            <div className="absolute inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

            {/* Modal */}
            <div className="relative bg-bg-surface border border-border-subtle rounded-xl shadow-2xl w-full max-w-lg mx-4 max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-border-subtle">
                    <h2 className="text-xl font-bold text-text-primary">
                        {isEditing ? "Edit Actor" : "Create Actor"}
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-1.5 rounded-full text-text-muted hover:bg-bg-elevated hover:text-text-primary transition-colors"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-6 space-y-5">
                    {error && (
                        <div className="p-3 rounded-md bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                            {error}
                        </div>
                    )}

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-text-secondary">Actor Name</label>
                        <input
                            type="text"
                            required
                            value={formData.actor_name}
                            onChange={(e) => handleChange("actor_name", e.target.value)}
                            placeholder="LinkedIn Logistics UAE"
                            className="block w-full px-3 py-2 border border-border-default rounded-md bg-bg-base text-text-primary placeholder-text-muted focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary text-sm transition-colors"
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-text-secondary">Actor ID (Apify)</label>
                        <input
                            type="text"
                            required
                            value={formData.actor_id}
                            onChange={(e) => handleChange("actor_id", e.target.value)}
                            placeholder="cheap_scraper/linkedin-job-scraper"
                            className="block w-full px-3 py-2 border border-border-default rounded-md bg-bg-base text-text-primary placeholder-text-muted focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary text-sm transition-colors font-mono"
                            disabled={isEditing}
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-text-secondary">Platform</label>
                            <select
                                value={formData.platform}
                                onChange={(e) => handleChange("platform", e.target.value)}
                                className="block w-full px-3 py-2 border border-border-default rounded-md bg-bg-base text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary text-sm transition-colors"
                            >
                                <option value="">Select...</option>
                                <option value="linkedin">LinkedIn</option>
                                <option value="naukrigulf">NaukriGulf</option>
                                <option value="bayt">Bayt</option>
                            </select>
                        </div>
                        <div className="space-y-1.5">
                            <label className="text-sm font-medium text-text-secondary">Domain</label>
                            <select
                                value={formData.domain}
                                onChange={(e) => handleChange("domain", e.target.value)}
                                className="block w-full px-3 py-2 border border-border-default rounded-md bg-bg-base text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary text-sm transition-colors"
                            >
                                <option value="">Select...</option>
                                <option value="logistics">Logistics / Supply Chain</option>
                                <option value="manufacturing">Manufacturing</option>
                                <option value="oil_gas">Oil & Gas</option>
                                <option value="construction">Construction</option>
                                <option value="retail">Retail / FMCG</option>
                                <option value="healthcare">Healthcare</option>
                                <option value="finance">Finance</option>
                            </select>
                        </div>
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-text-secondary">Normalizer Key</label>
                        <select
                            value={formData.normalizer_key}
                            onChange={(e) => handleChange("normalizer_key", e.target.value)}
                            className="block w-full px-3 py-2 border border-border-default rounded-md bg-bg-base text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary text-sm transition-colors"
                        >
                            <option value="">Select...</option>
                            <option value="linkedin">linkedin</option>
                            <option value="naukrigulf">naukrigulf</option>
                            <option value="bayt">bayt</option>
                        </select>
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-text-secondary">Frequency (days)</label>
                        <input
                            type="number"
                            min={1}
                            value={formData.frequency_days}
                            onChange={(e) => handleChange("frequency_days", parseInt(e.target.value) || 1)}
                            className="block w-full px-3 py-2 border border-border-default rounded-md bg-bg-base text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary text-sm transition-colors"
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-text-secondary">Input Template (JSON)</label>
                        <textarea
                            rows={5}
                            value={formData.apify_input_template}
                            onChange={(e) => handleChange("apify_input_template", e.target.value)}
                            className="block w-full px-3 py-2 border border-border-default rounded-md bg-bg-base text-text-primary placeholder-text-muted focus:outline-none focus:ring-1 focus:ring-accent-primary focus:border-accent-primary text-sm transition-colors font-mono"
                            placeholder='{"keyword": ["logistics"], "location": "UAE", "maxItems": 150}'
                        />
                    </div>

                    {/* Actions */}
                    <div className="flex justify-end gap-3 pt-2">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary transition-colors rounded-md hover:bg-bg-elevated"
                        >
                            Cancel
                        </button>
                        <Button
                            type="submit"
                            disabled={mutation.isPending}
                            className="px-6"
                        >
                            {mutation.isPending
                                ? "Saving..."
                                : isEditing ? "Update Actor" : "Create Actor"}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
