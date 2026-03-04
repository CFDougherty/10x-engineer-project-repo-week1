import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { useWindowVirtualizer } from '@tanstack/react-virtual';
import { useCollections } from '../contexts/CollectionsContext';
import { usePrompts, PROMPTS_QUERY_KEY } from '../contexts/PromptsContext';
import type { Prompt } from '../types/prompt';
import {
  Typography,
  CircularProgress,
  Alert,
  Box,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Fab,
} from '@mui/material';
import { Add as AddIcon, KeyboardArrowUp as KeyboardArrowUpIcon } from '@mui/icons-material';
import PromptFormDialog from '../components/PromptCreationDialog';
import SearchBar from '../components/SearchBar';
import Button from '../components/Button';
import PromptCard from '../components/PromptCard';
import VersionHistoryDialog from '../components/VersionHistoryDialog';
import { getPrompts, getPromptById } from '../services/apiClient';

const PAGE_SIZE = 20;

/** Split a flat array into rows of `cols` items each. */
function toRows<T>(items: T[], cols: number): T[][] {
  const rows: T[][] = [];
  for (let i = 0; i < items.length; i += cols) {
    rows.push(items.slice(i, i + cols));
  }
  return rows;
}

export default function PromptsPage() {
  // ── Search / filter state ────────────────────────────────────────────────
  const [searchInput, setSearchInput] = useState('');
  const [submittedSearch, setSubmittedSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [selectedCollection, setSelectedCollection] = useState('');
  const [semantic, setSemantic] = useState(false);

  // ── Dialog state ─────────────────────────────────────────────────────────
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editingPrompt, setEditingPrompt] = useState<Prompt | null>(null);
  const [historyPromptId, setHistoryPromptId] = useState<string | null>(null);

  const { collections } = useCollections();
  const { create, update, remove, refetch } = usePrompts();

  // ── Scroll tracking (scroll-to-top + position indicator) ─────────────────
  const [scrollY, setScrollY] = useState(0);
  useEffect(() => {
    const handle = () => setScrollY(window.scrollY);
    window.addEventListener('scroll', handle, { passive: true });
    return () => window.removeEventListener('scroll', handle);
  }, []);
  const showScrollTop = scrollY > 400;

  // ── Column count (responsive, measured via ResizeObserver) ────────────────
  // Using a callback ref so the observer is set up whenever the grid div mounts,
  // not just on the first render (which may be an isLoading early-return with no grid).
  const obsRef = useRef<ResizeObserver | null>(null);
  const [cols, setCols] = useState(1);
  const containerRef = useCallback((el: HTMLDivElement | null) => {
    obsRef.current?.disconnect();
    obsRef.current = null;
    if (!el) return;
    const obs = new ResizeObserver(([entry]) => {
      const w = entry.contentRect.width;
      setCols(w > 960 ? 4 : w > 640 ? 3 : w > 400 ? 2 : 1);
    });
    obs.observe(el);
    obsRef.current = obs;
  }, []);

  // ── Query key — changes trigger a fresh first-page fetch ─────────────────
  const queryKey = [
    ...PROMPTS_QUERY_KEY,
    { search: submittedSearch, filter, collectionId: selectedCollection, semantic },
  ];

  // ── Infinite query ────────────────────────────────────────────────────────
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetching,
    isFetchingNextPage,
    isLoading,
    error,
  } = useInfiniteQuery({
    queryKey,
    queryFn: ({ pageParam }) => {
      if (semantic && submittedSearch.trim()) {
        return getPrompts({
          search: submittedSearch,
          semantic: true,
          limit: PAGE_SIZE,
          offset: pageParam ? parseInt(pageParam as string, 10) : 0,
          ...(selectedCollection && selectedCollection !== '__none__'
            ? { collection_id: selectedCollection }
            : {}),
        }).then((r) => r.data);
      }
      return getPrompts({
        limit: PAGE_SIZE,
        cursor: pageParam as string | undefined,
        search: submittedSearch || undefined,
        filter: filter !== 'all' ? filter : undefined,
        // "__none__" is handled client-side after fetch
        collection_id:
          selectedCollection && selectedCollection !== '__none__'
            ? selectedCollection
            : undefined,
        fuzzy: true,
      }).then((r) => r.data);
    },
    getNextPageParam: (lastPage) => lastPage.next_cursor ?? undefined,
    initialPageParam: undefined as string | undefined,
  });

  // Flatten all loaded pages into a single array
  const allPrompts: Prompt[] = useMemo(
    () => data?.pages.flatMap((p) => p.prompts) ?? [],
    [data],
  );

  // "__none__" = prompts with no collection — filter client-side after fetch
  const displayedPrompts = useMemo(
    () =>
      selectedCollection === '__none__'
        ? allPrompts.filter((p) => !p.collection_id)
        : allPrompts,
    [allPrompts, selectedCollection],
  );

  // ── Handlers ──────────────────────────────────────────────────────────────
  const handleSearch = () => setSubmittedSearch(searchInput);

  const handleSemanticToggle = (next: boolean) => {
    setSemantic(next);
    setSubmittedSearch(searchInput);
  };

  useEffect(() => {
    const timer = setTimeout(() => {
      setSubmittedSearch(searchInput);
    }, 500);
    return () => clearTimeout(timer);
  }, [searchInput]);

  const handleEdit = async (promptId: string) => {
    // List responses carry truncated content; fetch the full prompt before editing
    const full = await getPromptById(promptId).then((r) => r.data as Prompt);
    setEditingPrompt(full);
    setEditDialogOpen(true);
  };

  const handleEditSubmit = async (promptData: {
    title: string;
    content: string;
    description?: string;
    tags: string[];
    collection_id?: string;
  }) => {
    if (!editingPrompt) return;
    await update(editingPrompt.id, promptData);
  };

  const handleDelete = async (id: string) => remove(id);

  // ── Virtualiser ───────────────────────────────────────────────────────────
  const rows = useMemo(() => toRows(displayedPrompts, cols), [displayedPrompts, cols]);
  // +1 sentinel row at the bottom to trigger the next page fetch
  const rowCount = rows.length + (hasNextPage || isFetchingNextPage ? 1 : 0);

  const virtualizer = useWindowVirtualizer({
    count: rowCount,
    estimateSize: () => 370, // px — measured dynamically after first render
    overscan: 3,
  });

  // IntersectionObserver on the sentinel row → fetchNextPage
  const sentinelRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (!node) return;
      const obs = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting && hasNextPage && !isFetchingNextPage) {
            fetchNextPage();
          }
        },
        { rootMargin: '200px' },
      );
      obs.observe(node);
      return () => obs.disconnect();
    },
    [hasNextPage, isFetchingNextPage, fetchNextPage],
  );

  // ── Early returns ─────────────────────────────────────────────────────────
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{(error as Error).message}</Alert>;
  }

  // ── Render ────────────────────────────────────────────────────────────────
  return (
    <div>
      {/* Header: search bar + collection selector + New Prompt button */}
      <Box
        display="flex"
        flexDirection={{ xs: 'column', sm: 'row' }}
        justifyContent="space-between"
        alignItems={{ xs: 'stretch', sm: 'center' }}
        mb={4}
        gap={2}
      >
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" gutterBottom>Prompts</Typography>
          <Box display="flex" alignItems="center" gap={2} mb={2} flexWrap="wrap">
            <SearchBar
              value={searchInput}
              onChange={setSearchInput}
              onSearch={handleSearch}
              onClear={() => { setSearchInput(''); setSubmittedSearch(''); }}
              searchField={filter}
              onSearchFieldChange={setFilter}
              placeholder="Search prompts..."
              loading={isFetching && !isFetchingNextPage}
              semantic={semantic}
              onSemanticChange={handleSemanticToggle}
              sx={{ flexGrow: 1 }}
            />
            <FormControl sx={{ minWidth: { xs: '100%', sm: 200 } }}>
              <InputLabel>Filter by Collection</InputLabel>
              <Select
                value={selectedCollection}
                label="Filter by Collection"
                onChange={(e) => setSelectedCollection(e.target.value)}
                sx={{ backgroundColor: 'background.paper', borderRadius: 1 }}
                MenuProps={{
                  PaperProps: {
                    sx: {
                      bgcolor: 'background.paper',
                      '& .MuiMenuItem-root': { color: 'text.primary' },
                    },
                  },
                }}
              >
                <MenuItem value="">All Collections</MenuItem>
                <MenuItem value="__none__">Not in any collection</MenuItem>
                {collections.map((c) => (
                  <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
          {semantic && (
            <Typography variant="caption" color="white">
              Semantic mode — press Enter or click search to query by meaning
            </Typography>
          )}
        </Box>
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
          sx={{ ml: { xs: 0, sm: 2 }, alignSelf: { xs: 'flex-start', sm: 'center' }, flexShrink: 0 }}
        >
          New Prompt
        </Button>
      </Box>

      {/* Dialogs */}
      <PromptFormDialog
        open={createDialogOpen}
        onClose={() => setCreateDialogOpen(false)}
        mode="create"
        onSubmit={async (promptData) => { await create(promptData); }}
        onPromptCreated={refetch}
      />
      <PromptFormDialog
        open={editDialogOpen}
        onClose={() => setEditDialogOpen(false)}
        mode="edit"
        initialData={editingPrompt || undefined}
        onSubmit={handleEditSubmit}
      />
      <VersionHistoryDialog
        open={historyPromptId !== null}
        onClose={() => setHistoryPromptId(null)}
        promptId={historyPromptId ?? ''}
        onRestored={refetch}
      />

      {/* Empty state */}
      {displayedPrompts.length === 0 && !isFetching && (
        <Alert severity="info">
          {semantic && submittedSearch.trim()
            ? 'No semantically similar prompts found. Try a different query or run backfill if embeddings are not yet generated.'
            : 'No prompts found. Create your first prompt!'}
        </Alert>
      )}

      {/* Position indicator */}
      {(() => {
        const virtualItems = virtualizer.getVirtualItems();
        const lastContentRow = [...virtualItems].reverse().find(v => v.index < rows.length);
        const currentIndex = lastContentRow
          ? Math.min((lastContentRow.index + 1) * cols, displayedPrompts.length)
          : 0;
        const apiTotal = data?.pages.at(-1)?.total ?? 0;
        const isNoneFilter = selectedCollection === '__none__';
        const displayTotal = isNoneFilter
          ? `${displayedPrompts.length}${hasNextPage ? '+' : ''}`
          : apiTotal;
        return displayedPrompts.length > 0 ? (
          <Box
            sx={{
              position: 'fixed',
              bottom: 24,
              left: 24,
              zIndex: 1200,
              bgcolor: 'background.paper',
              border: '1px solid',
              borderColor: 'divider',
              borderRadius: 2,
              px: 1.5,
              py: 0.5,
              typography: 'caption',
              color: 'text.secondary',
              boxShadow: 1,
              userSelect: 'none',
            }}
          >
            {currentIndex} / {displayTotal}
          </Box>
        ) : null;
      })()}

      {/* Scroll-to-top button */}
      {showScrollTop && (
        <Fab
          size="small"
          onClick={() => window.scrollTo({ top: 0, behavior: 'smooth' })}
          sx={{ position: 'fixed', bottom: 24, right: 24, zIndex: 1200 }}
          aria-label="Scroll to top"
        >
          <KeyboardArrowUpIcon />
        </Fab>
      )}

      {/* Virtualised card grid */}
      <div ref={containerRef}>
        <div
          style={{
            height: `${virtualizer.getTotalSize()}px`,
            position: 'relative',
            width: '100%',
          }}
        >
          {virtualizer.getVirtualItems().map((virtualRow) => {
            const isSentinel = virtualRow.index >= rows.length;
            return (
              <div
                key={virtualRow.key}
                data-index={virtualRow.index}
                ref={isSentinel ? sentinelRef : virtualizer.measureElement}
                style={{
                  position: 'absolute',
                  top: 0,
                  left: 0,
                  width: '100%',
                  transform: `translateY(${virtualRow.start}px)`,
                  paddingBottom: '24px',
                }}
              >
                {isSentinel ? (
                  <Box display="flex" justifyContent="center" py={2}>
                    {isFetchingNextPage && <CircularProgress size={28} />}
                  </Box>
                ) : (
                  <Box
                    display="grid"
                    gridTemplateColumns={`repeat(${cols}, 1fr)`}
                    gap={{ xs: 2, sm: 3 }}
                  >
                    {rows[virtualRow.index].map((prompt) => (
                      <PromptCard
                        key={prompt.id}
                        prompt={prompt}
                        cols={cols}
                        collectionName={
                          collections.find((c) => c.id === prompt.collection_id)?.name
                        }
                        onEdit={handleEdit}
                        onDelete={handleDelete}
                        onViewHistory={(id) => setHistoryPromptId(id)}
                      />
                    ))}
                  </Box>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
