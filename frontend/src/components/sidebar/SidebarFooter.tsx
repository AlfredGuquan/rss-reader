import { useState } from 'react';
import { Plus, FileUp, FolderPlus, Rss } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
} from '@/components/ui/dropdown-menu';
import { AddFeedDialog } from '@/components/feed-management/AddFeedDialog';
import { ImportOpmlDialog } from '@/components/feed-management/ImportOpmlDialog';
import { CreateGroupDialog } from '@/components/group-management/CreateGroupDialog';

export function SidebarFooter() {
  const [addFeedOpen, setAddFeedOpen] = useState(false);
  const [importOpmlOpen, setImportOpmlOpen] = useState(false);
  const [createGroupOpen, setCreateGroupOpen] = useState(false);

  return (
    <div className="border-t p-2">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
            <Plus className="h-4 w-4" />
            Add
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent align="start" side="top">
          <DropdownMenuItem onClick={() => setAddFeedOpen(true)}>
            <Rss />
            Add Feed
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setImportOpmlOpen(true)}>
            <FileUp />
            Import OPML
          </DropdownMenuItem>
          <DropdownMenuItem onClick={() => setCreateGroupOpen(true)}>
            <FolderPlus />
            Create Group
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>

      <AddFeedDialog open={addFeedOpen} onOpenChange={setAddFeedOpen} />
      <ImportOpmlDialog open={importOpmlOpen} onOpenChange={setImportOpmlOpen} />
      <CreateGroupDialog open={createGroupOpen} onOpenChange={setCreateGroupOpen} />
    </div>
  );
}
