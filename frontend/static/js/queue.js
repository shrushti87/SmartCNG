/**
 * SmartCNG – Queue/Crowd Update Module
 * Handles crowd reporting and voting on queue updates.
 */

const QueueUI = {
    // ─── Load Queue Updates for a Station ───────────────
    async loadQueueUpdates(stationId, containerId = 'queue-updates') {
        const container = document.getElementById(containerId);
        if (!container) return;

        try {
            const data = await API.getLatestQueue(stationId);
            const updates = data.updates || [];

            if (updates.length === 0) {
                container.innerHTML = `
                    <div class="empty-state" style="padding: 20px;">
                        <p>No recent crowd updates. Be the first to report!</p>
                    </div>
                `;
                return;
            }

            container.innerHTML = updates.map(u => `
                <div class="queue-update-item ${u.is_expired ? 'expired' : ''}">
                    <div class="update-avatar">${u.username.charAt(0).toUpperCase()}</div>
                    <div class="update-content">
                        <div class="update-header">
                            <span class="update-username">${u.username}</span>
                            <span class="update-time">${Utils.formatTimeAgo(u.timestamp)}</span>
                            ${u.is_expired ? '<span class="chip">Expired</span>' : ''}
                        </div>
                        <div class="update-details">
                            ${Utils.getStatusEmoji(u.availability)} ${Utils.getStatusLabel(u.availability)}
                            · 🚗 ${u.queue_length} vehicles
                            ${u.comment ? `<br><em>"${u.comment}"</em>` : ''}
                        </div>
                        <div class="vote-buttons">
                            <button class="vote-btn ${u.user_vote === 'up' ? 'voted' : ''}"
                                onclick="QueueUI.vote(${u.id}, 'up')">
                                👍 ${u.upvotes}
                            </button>
                            <button class="vote-btn ${u.user_vote === 'down' ? 'voted' : ''}"
                                onclick="QueueUI.vote(${u.id}, 'down')">
                                👎 ${u.downvotes}
                            </button>
                            <span class="chip">Reliability: ${u.reliability_score}%</span>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load queue updates:', error);
        }
    },

    // ─── Submit Queue Update ────────────────────────────
    async submitUpdate(stationId) {
        if (!API.isLoggedIn()) {
            Utils.showToast('Please login to report crowd status', 'error');
            return;
        }

        const queueLength = document.getElementById('queue-length')?.value;
        const availability = document.getElementById('queue-availability')?.value;
        const comment = document.getElementById('queue-comment')?.value;

        if (!queueLength || queueLength < 0) {
            Utils.showToast('Please enter a valid queue length', 'error');
            return;
        }

        try {
            await API.submitQueueUpdate({
                station: stationId,
                queue_length: parseInt(queueLength),
                availability: availability,
                comment: comment,
            });

            Utils.showToast('Queue update submitted!', 'success');
            Utils.closeModal('queue-update-modal');
            
            // Reload updates in the detail list if it exists
            this.loadQueueUpdates(stationId);

            // If on detail page, reload station info too
            if (typeof loadStationDetail === 'function') {
                loadStationDetail();
            }

            // If on home page, refresh map and station list
            if (window.SmartMap && typeof SmartMap.loadStations === 'function') {
                SmartMap.loadStations();
            }
        } catch (error) {
            const msg = error.data?.error || 'Failed to submit update';
            Utils.showToast(msg, 'error');
        }
    },

    // ─── Vote on Queue Update ───────────────────────────
    async vote(updateId, voteType) {
        if (!API.isLoggedIn()) {
            Utils.showToast('Please login to vote', 'error');
            return;
        }

        try {
            await API.voteOnUpdate(updateId, voteType);
            // Reload the queue updates for the current station
            const stationId = document.getElementById('queue-updates')?.dataset.stationId;
            if (stationId) {
                this.loadQueueUpdates(stationId);
            }
        } catch (error) {
            Utils.showToast('Failed to record vote', 'error');
        }
    },

    // ─── Open Queue Update Modal ────────────────────────
    openUpdateModal(stationId, stationName) {
        if (!API.isLoggedIn()) {
            Utils.showToast('Please login to report crowd status', 'error');
            setTimeout(() => window.location.href = '/login/', 1500);
            return;
        }

        const modal = document.getElementById('queue-update-modal');
        if (!modal) return;

        modal.querySelector('.queue-station-name').textContent = stationName;
        modal.dataset.stationId = stationId;

        // Reset form
        const form = modal.querySelector('form');
        if (form) form.reset();

        Utils.openModal('queue-update-modal');
    },
};
