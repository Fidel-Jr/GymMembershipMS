
(function($) {

	"use strict";

	var fullHeight = function() {
		$('.js-fullheight').css('height', $(window).height());
		$(window).resize(function(){
			$('.js-fullheight').css('height', $(window).height());
		});
	};
	fullHeight();

	$('#sidebarCollapse').on('click', function () {
		$('#sidebar').toggleClass('active');
	});

	// Delegated event for view-membership-btn to ensure modal opens
	$(document).on('click', '.view-membership-btn', function() {
		var row = $(this).closest('tr');
		$('#membershipDetailId').text(row.find('td').eq(0).text());
		$('#membershipDetailMember').text(row.find('td').eq(1).text());
		$('#membershipDetailPlan').text(row.find('td').eq(2).text());
		$('#membershipDetailDuration').text(row.find('td').eq(3).text() + ' to ' + row.find('td').eq(4).text());
		$('#membershipDetailStartDate').text(row.find('td').eq(3).text());
		$('#membershipDetailEndDate').text(row.find('td').eq(4).text());
		$('#membershipDetailStatus').html(row.find('td').eq(5).html());
		$('#membershipDetailPayment').html(row.find('td').eq(6).html());
		// Show modal (for Bootstrap 5)
		var modal = new bootstrap.Modal(document.getElementById('viewModal'));
		modal.show();
	});

})(jQuery);
