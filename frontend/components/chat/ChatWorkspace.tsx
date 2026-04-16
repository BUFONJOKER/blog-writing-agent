"use client";

import { AuthRequiredCard } from "@/components/chat/AuthRequiredCard";
import { BottomComposer } from "@/components/chat/BottomComposer";
import { ChatConversation } from "@/components/chat/ChatConversation";
import { ChatSidebar } from "@/components/chat/ChatSidebar";
import { MenuButton } from "@/components/chat/MenuButton";
import { useChatWorkflow } from "@/components/chat/useChatWorkflow";

export function ChatWorkspace() {
    const workflow = useChatWorkflow();

    return (
        <main className="min-h-screen bg-black text-white">
            <MenuButton onOpen={() => workflow.setDrawerOpen(true)} />

            {workflow.drawerOpen && (
                <button
                    type="button"
                    aria-label="Close menu backdrop"
                    onClick={() => workflow.setDrawerOpen(false)}
                    className="fixed inset-0 z-30 bg-black/60"
                />
            )}

            <ChatSidebar
                drawerOpen={workflow.drawerOpen}
                isLoggedIn={workflow.isLoggedIn}
                isCreatingChat={workflow.isCreatingChat}
                threadsLoading={workflow.threadsLoading}
                threads={workflow.threads}
                activeThreadId={workflow.activeThreadId}
                userEmail={workflow.userEmail}
                userName={workflow.userName}
                onClose={() => workflow.setDrawerOpen(false)}
                onQuickNewChat={workflow.handleQuickNewChat}
                onSelectThread={(threadId) => {
                    workflow.setDrawerOpen(false);
                    workflow.setActiveThreadId(threadId);
                }}
                onDeleteThread={workflow.handleDeleteThread}
                onLogout={workflow.handleLogout}
            />

            <section className="mx-auto flex min-h-screen w-full max-w-5xl flex-col px-4 pb-36 pt-16 md:px-8 md:pb-40">
                <header className="mb-6 rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 text-center">
                    <p className="mx-auto max-w-3xl text-sm text-zinc-400">
                        This AI-assisted blog creation workflow includes research, planning, drafting, editing, critique review, and final human approval before publication.
                        The process typically takes around 10-15 minutes, depending on the level of research required.
                        Blogs that do not require research are completed faster.
                        Please note that we use the open-source Qwen 3.5 model via Ollama, so inference speed may be slower compared to cloud-based proprietary models.
                    </p>
                </header>

                {workflow.authReady && workflow.isLoggedIn && workflow.ollamaSetupNotice && (
                    <div className="mb-6 rounded-2xl border border-amber-500/40 bg-amber-950/30 p-5 text-left">
                        <div className="flex items-start justify-between gap-4">
                            <div>
                                <h2 className="text-sm font-semibold text-amber-200">{workflow.ollamaSetupNotice.title}</h2>
                                <p className="mt-2 text-sm text-amber-100/90">{workflow.ollamaSetupNotice.description}</p>
                                <ol className="mt-3 list-decimal space-y-1 pl-5 text-sm text-amber-100">
                                    {workflow.ollamaSetupNotice.steps.map((step) => (
                                        <li key={step}>
                                            <code className="rounded bg-black/40 px-2 py-0.5 text-amber-50">{step}</code>
                                        </li>
                                    ))}
                                </ol>
                            </div>
                            <button
                                type="button"
                                onClick={workflow.dismissOllamaSetupNotice}
                                className="rounded-md border border-amber-300/40 px-3 py-1 text-xs text-amber-100 transition hover:bg-amber-200/10"
                            >
                                Dismiss
                            </button>
                        </div>
                    </div>
                )}

                {!workflow.authReady && (
                    <div className="rounded-2xl border border-zinc-800 bg-zinc-900/60 p-6 text-sm text-zinc-400">Checking session...</div>
                )}

                {workflow.authReady && !workflow.isLoggedIn && <AuthRequiredCard />}

                {workflow.authReady && workflow.isLoggedIn && (
                    <ChatConversation
                        globalError={workflow.globalError}
                        activeThreadPrompt={workflow.activeThreadPrompt}
                        activeThreadId={workflow.activeThreadId}
                        activeThreadLoading={workflow.activeThreadLoading}
                        activeThreadMarkdown={workflow.activeThreadMarkdown}
                        isStreaming={workflow.isStreaming}
                        currentNode={workflow.currentNode}
                        workflowNodes={workflow.workflowNodes}
                        workflowTotalNodes={workflow.workflowTotalNodes}
                        workflowStartTime={workflow.workflowStartTime}
                        workflowTotalTime={workflow.workflowTotalTime}
                        waitingForApproval={workflow.waitingForApproval}
                        approvalSubmitting={workflow.approvalSubmitting}
                        activeApprovalAction={workflow.activeApprovalAction}
                        criticOutput={workflow.criticOutput}
                        editedDraft={workflow.editedDraft}
                        onApprove={() => void workflow.handleReviewDecision(true)}
                        onReject={() => void workflow.handleReviewDecision(false)}
                    />
                )}
            </section>

            {workflow.isLoggedIn && (
                <BottomComposer
                    prompt={workflow.prompt}
                    isCreatingChat={workflow.isCreatingChat}
                    disabled={Boolean(workflow.activeThreadId)}
                    disabledHint="This chat is complete. Click New Chat to start a fresh one."
                    onPromptChange={workflow.setPrompt}
                    onSubmit={workflow.handlePromptSubmit}
                />
            )}
        </main>
    );
}