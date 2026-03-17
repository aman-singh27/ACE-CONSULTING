import { useState } from "react";
import { ActorTable } from "../../components/actors/ActorTable";
import { ActorFormModal } from "../../components/actors/ActorFormModal";
import { Button } from "../../components/ui/Button";
import { Plus } from "lucide-react";
import type { ActorItem } from "../../components/actors/ActorTable";

export function ActorsPage() {
    const [showModal, setShowModal] = useState(false);
    const [editingActor, setEditingActor] = useState<ActorItem | null>(null);

    const handleEdit = (actor: ActorItem) => {
        setEditingActor(actor);
        setShowModal(true);
    };

    const handleCreate = () => {
        setEditingActor(null);
        setShowModal(true);
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingActor(null);
    };

    return (
        <div className="flex flex-col h-full w-full">
            {/* Header */}
            <div className="mb-6 flex justify-between items-end shrink-0">
                <div>
                    <h1 className="text-3xl font-bold tracking-tight text-text-primary">Actors</h1>
                    <p className="text-text-secondary mt-1">Manage scraping actors and trigger runs.</p>
                </div>
                <Button onClick={handleCreate} className="flex items-center gap-2">
                    <Plus size={16} />
                    Create Actor
                </Button>
            </div>

            {/* Table */}
            <div className="flex-grow min-h-0 overflow-auto">
                <ActorTable onEdit={handleEdit} />
            </div>

            {/* Modal */}
            {showModal && (
                <ActorFormModal
                    actor={editingActor}
                    onClose={handleCloseModal}
                />
            )}
        </div>
    );
}
